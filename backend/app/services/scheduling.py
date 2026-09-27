from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus, ScheduleStatus
from app.models.post import Post
from app.models.schedule import Schedule
from app.repositories.post import PostRepository
from app.repositories.publishing_log import PublishingLogRepository
from app.repositories.schedule import ScheduleRepository
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class SchedulingService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.schedules = ScheduleRepository(session)
        self.posts = PostRepository(session)
        self.logs = PublishingLogRepository(session)

    def create(self, user_id: UUID, payload: ScheduleCreate) -> Schedule:
        post = self._post(user_id, payload.post_id)
        if post.status != PostStatus.APPROVED:
            raise ApplicationError(
                "POST_NOT_APPROVED", "Only approved posts can be scheduled.", 409
            )
        if self.schedules.active_for_post(user_id, post.id) is not None:
            raise ApplicationError(
                "POST_ALREADY_SCHEDULED", "Post already has an active schedule.", 409
            )
        scheduled_for = payload.scheduled_for.astimezone(UTC)
        self._ensure_future(scheduled_for)
        schedule = self.schedules.create_for_user(
            user_id,
            post_id=post.id,
            recurrence=payload.recurrence,
            status=ScheduleStatus.ACTIVE,
            timezone=payload.timezone,
            scheduled_for=scheduled_for,
            next_run_at=scheduled_for,
            recurrence_rule=payload.recurrence_details(),
        )
        post.status = PostStatus.SCHEDULED
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def list(
        self, user_id: UUID, *, status: ScheduleStatus | None, start: datetime | None,
        end: datetime | None, offset: int, limit: int
    ) -> tuple[list[Schedule], int]:
        return self.schedules.list_filtered_for_user(
            user_id,
            status=status,
            start=self._utc(start),
            end=self._utc(end),
            offset=offset,
            limit=limit,
        )

    def get(self, user_id: UUID, schedule_id: UUID) -> Schedule:
        schedule = self.schedules.get_for_user(schedule_id, user_id)
        if schedule is None:
            raise ApplicationError("SCHEDULE_NOT_FOUND", "Schedule not found.", 404)
        return schedule

    def reschedule(self, user_id: UUID, schedule_id: UUID, payload: ScheduleUpdate) -> Schedule:
        schedule = self.get(user_id, schedule_id)
        if schedule.status not in {ScheduleStatus.ACTIVE, ScheduleStatus.PAUSED}:
            raise ApplicationError(
                "SCHEDULE_NOT_EDITABLE",
                "Completed or cancelled schedules cannot be changed.",
                409,
            )
        scheduled_for = payload.scheduled_for.astimezone(UTC)
        self._ensure_future(scheduled_for)
        schedule.scheduled_for = scheduled_for
        schedule.next_run_at = scheduled_for if schedule.status == ScheduleStatus.ACTIVE else None
        schedule.timezone = payload.timezone
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def cancel(self, user_id: UUID, schedule_id: UUID) -> Schedule:
        schedule = self.get(user_id, schedule_id)
        if schedule.status not in {ScheduleStatus.ACTIVE, ScheduleStatus.PAUSED}:
            raise ApplicationError("SCHEDULE_NOT_CANCELLABLE", "Schedule is already final.", 409)
        schedule.status = ScheduleStatus.CANCELLED
        schedule.next_run_at = None
        post = self._post(user_id, schedule.post_id)
        if post.status == PostStatus.SCHEDULED:
            post.status = PostStatus.APPROVED
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def pause(self, user_id: UUID, schedule_id: UUID) -> Schedule:
        schedule = self.get(user_id, schedule_id)
        if schedule.status != ScheduleStatus.ACTIVE:
            raise ApplicationError(
                "SCHEDULE_NOT_ACTIVE", "Only active schedules can be paused.", 409
            )
        schedule.status = ScheduleStatus.PAUSED
        schedule.next_run_at = None
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def resume(self, user_id: UUID, schedule_id: UUID) -> Schedule:
        schedule = self.get(user_id, schedule_id)
        if schedule.status != ScheduleStatus.PAUSED:
            raise ApplicationError(
                "SCHEDULE_NOT_PAUSED", "Only paused schedules can be resumed.", 409
            )
        self._ensure_future(schedule.scheduled_for)
        schedule.status = ScheduleStatus.ACTIVE
        schedule.next_run_at = schedule.scheduled_for
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def retry_failed(self, user_id: UUID, schedule_id: UUID) -> Schedule:
        schedule = self.get(user_id, schedule_id)
        if schedule.status != ScheduleStatus.COMPLETED or schedule.post.status != PostStatus.FAILED:
            raise ApplicationError(
                "SCHEDULE_NOT_RETRYABLE", "Only failed publishing schedules can be retried.", 409
            )
        latest = self.logs.latest_for_post(schedule.post_id)
        metadata = latest.response_metadata if latest is not None else None
        if not metadata or metadata.get("retry_safe") is not True:
            raise ApplicationError(
                "PUBLISH_OUTCOME_UNCERTAIN",
                "This attempt cannot be retried safely because LinkedIn may have published it.",
                409,
            )
        if schedule.attempt_count >= self.settings.publishing_max_attempts:
            raise ApplicationError(
                "PUBLISH_RETRY_LIMIT_REACHED", "Publishing retry limit reached.", 409
            )
        schedule.status = ScheduleStatus.ACTIVE
        schedule.post.status = PostStatus.SCHEDULED
        schedule.next_run_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def _post(self, user_id: UUID, post_id: UUID) -> Post:
        post = self.posts.get_for_user(post_id, user_id)
        if post is None:
            raise ApplicationError("POST_NOT_FOUND", "Post not found.", 404)
        return post

    @staticmethod
    def _ensure_future(value: datetime) -> None:
        normalized = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        if normalized <= datetime.now(UTC):
            raise ApplicationError("SCHEDULE_IN_PAST", "Schedule time must be in the future.", 422)

    @staticmethod
    def _utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ApplicationError(
                "INVALID_DATE_RANGE", "Date filters must include a UTC offset.", 422
            )
        return value.astimezone(UTC)
