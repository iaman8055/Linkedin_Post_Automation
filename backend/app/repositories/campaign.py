from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.campaign import Campaign
from app.models.enums import CampaignStatus
from app.repositories.base import UserOwnedRepository


class CampaignRepository(UserOwnedRepository[Campaign]):
    def __init__(self, session: Session) -> None:
        super().__init__(Campaign, session)

    def list_filtered_for_user(
        self,
        user_id: UUID,
        *,
        status: CampaignStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Campaign], int]:
        filters = self.ownership_filters(user_id)
        if status is not None:
            filters.append(Campaign.status == status)
        statement = (
            select(Campaign)
            .options(selectinload(Campaign.posts))
            .where(*filters)
            .order_by(Campaign.created_at.desc(), Campaign.id.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count()).select_from(Campaign).where(*filters)
        return list(self.session.scalars(statement)), self.session.scalar(count_statement) or 0

    def get_with_posts_for_user(self, campaign_id: UUID, user_id: UUID) -> Campaign | None:
        statement = (
            select(Campaign)
            .options(selectinload(Campaign.posts))
            .execution_options(populate_existing=True)
            .where(Campaign.id == campaign_id, *self.ownership_filters(user_id))
        )
        return self.session.scalar(statement)
