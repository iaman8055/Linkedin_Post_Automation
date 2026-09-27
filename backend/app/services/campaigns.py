from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.campaign import Campaign
from app.models.enums import CampaignStatus, PostStatus, ScheduleStatus
from app.models.post import Post
from app.models.writing_profile import WritingProfile
from app.repositories.campaign import CampaignRepository
from app.repositories.post import PostRepository
from app.repositories.schedule import ScheduleRepository
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate

ALLOWED_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.DRAFT: {CampaignStatus.ACTIVE, CampaignStatus.CANCELLED},
    CampaignStatus.ACTIVE: {
        CampaignStatus.PAUSED,
        CampaignStatus.COMPLETED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.PAUSED: {
        CampaignStatus.ACTIVE,
        CampaignStatus.COMPLETED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.COMPLETED: set(),
    CampaignStatus.CANCELLED: set(),
}


class CampaignService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.campaigns = CampaignRepository(session)
        self.posts = PostRepository(session)
        self.schedules = ScheduleRepository(session)

    def create(self, user_id: UUID, payload: CampaignCreate) -> Campaign:
        self._validate_writing_profile(user_id, payload.writing_profile_id)
        values = payload.model_dump()
        values["description"] = self._normalize_optional(values["description"])
        campaign = self.campaigns.create_for_user(
            user_id, **values, status=CampaignStatus.DRAFT
        )
        self.session.commit()
        return self.get(user_id, campaign.id)

    def list(
        self,
        user_id: UUID,
        *,
        status: CampaignStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Campaign], int]:
        return self.campaigns.list_filtered_for_user(
            user_id, status=status, offset=offset, limit=limit
        )

    def get(self, user_id: UUID, campaign_id: UUID) -> Campaign:
        campaign = self.campaigns.get_with_posts_for_user(campaign_id, user_id)
        if campaign is None:
            raise ApplicationError("CAMPAIGN_NOT_FOUND", "Campaign not found.", 404)
        return campaign

    def update(
        self, user_id: UUID, campaign_id: UUID, payload: CampaignUpdate
    ) -> Campaign:
        campaign = self.get(user_id, campaign_id)
        self._ensure_mutable(campaign)
        changes = payload.model_dump(exclude_unset=True)
        if "writing_profile_id" in changes:
            self._validate_writing_profile(user_id, changes["writing_profile_id"])
        if "description" in changes:
            changes["description"] = self._normalize_optional(changes["description"])
        for field, value in changes.items():
            setattr(campaign, field, value)
        self.session.commit()
        return self.get(user_id, campaign_id)

    def transition(
        self, user_id: UUID, campaign_id: UUID, target: CampaignStatus
    ) -> Campaign:
        campaign = self.get(user_id, campaign_id)
        if target not in ALLOWED_TRANSITIONS[campaign.status]:
            raise ApplicationError(
                "INVALID_CAMPAIGN_TRANSITION",
                f"Campaign cannot move from {campaign.status.value} to {target.value}.",
                409,
            )
        campaign.status = target
        self._sync_campaign_schedules(user_id, campaign_id, target)
        self.session.commit()
        return self.get(user_id, campaign_id)

    def delete(self, user_id: UUID, campaign_id: UUID) -> None:
        campaign = self.get(user_id, campaign_id)
        if campaign.status != CampaignStatus.DRAFT:
            raise ApplicationError(
                "CAMPAIGN_NOT_DELETABLE", "Only draft campaigns can be deleted.", 409
            )
        self.campaigns.delete(campaign)
        self.session.commit()

    def add_post(self, user_id: UUID, campaign_id: UUID, post_id: UUID) -> Campaign:
        campaign = self.get(user_id, campaign_id)
        self._ensure_mutable(campaign)
        post = self._get_post(user_id, post_id)
        post.campaign_id = campaign.id
        self.session.commit()
        return self.get(user_id, campaign_id)

    def remove_post(self, user_id: UUID, campaign_id: UUID, post_id: UUID) -> Campaign:
        campaign = self.get(user_id, campaign_id)
        self._ensure_mutable(campaign)
        post = self._get_post(user_id, post_id)
        if post.campaign_id != campaign.id:
            raise ApplicationError(
                "POST_NOT_IN_CAMPAIGN", "Post does not belong to this campaign.", 409
            )
        post.campaign_id = None
        self.session.commit()
        return self.get(user_id, campaign_id)

    @staticmethod
    def to_response(campaign: Campaign) -> CampaignResponse:
        return CampaignResponse.model_validate(
            {**campaign.__dict__, "post_count": len(campaign.posts)}
        )

    def _validate_writing_profile(self, user_id: UUID, profile_id: UUID | None) -> None:
        if profile_id is None:
            return
        statement = select(WritingProfile.id).where(
            WritingProfile.id == profile_id, WritingProfile.user_id == user_id
        )
        if self.session.scalar(statement) is None:
            raise ApplicationError("WRITING_PROFILE_NOT_FOUND", "Writing profile not found.", 404)

    def _get_post(self, user_id: UUID, post_id: UUID) -> Post:
        post = self.posts.get_for_user(post_id, user_id)
        if post is None:
            raise ApplicationError("POST_NOT_FOUND", "Post not found.", 404)
        return post

    @staticmethod
    def _ensure_mutable(campaign: Campaign) -> None:
        if campaign.status in {CampaignStatus.COMPLETED, CampaignStatus.CANCELLED}:
            raise ApplicationError(
                "CAMPAIGN_NOT_EDITABLE", "Completed or cancelled campaigns cannot be changed.", 409
            )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _sync_campaign_schedules(
        self, user_id: UUID, campaign_id: UUID, target: CampaignStatus
    ) -> None:
        schedules = self.schedules.for_campaign(user_id, campaign_id)
        if target == CampaignStatus.PAUSED:
            for schedule in schedules:
                if schedule.status == ScheduleStatus.ACTIVE:
                    schedule.status = ScheduleStatus.PAUSED
                    schedule.next_run_at = None
        elif target == CampaignStatus.ACTIVE:
            for schedule in schedules:
                if schedule.status == ScheduleStatus.PAUSED:
                    scheduled_for = schedule.scheduled_for
                    normalized = (
                        scheduled_for.replace(tzinfo=UTC)
                        if scheduled_for.tzinfo is None
                        else scheduled_for.astimezone(UTC)
                    )
                    if normalized > datetime.now(UTC):
                        schedule.status = ScheduleStatus.ACTIVE
                        schedule.next_run_at = schedule.scheduled_for
        elif target == CampaignStatus.CANCELLED:
            for schedule in schedules:
                if schedule.status in {ScheduleStatus.ACTIVE, ScheduleStatus.PAUSED}:
                    schedule.status = ScheduleStatus.CANCELLED
                    schedule.next_run_at = None
                    if schedule.post.status == PostStatus.SCHEDULED:
                        schedule.post.status = PostStatus.APPROVED
