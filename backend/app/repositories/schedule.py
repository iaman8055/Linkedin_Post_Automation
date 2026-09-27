from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PostStatus, ScheduleStatus
from app.models.post import Post
from app.models.schedule import Schedule
from app.repositories.base import UserOwnedRepository


class ScheduleRepository(UserOwnedRepository[Schedule]):
    def __init__(self, session: Session) -> None:
        super().__init__(Schedule, session)

    def list_filtered_for_user(
        self,
        user_id: UUID,
        *,
        status: ScheduleStatus | None,
        start: datetime | None,
        end: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Schedule], int]:
        filters = [Schedule.user_id == user_id]
        if status is not None:
            filters.append(Schedule.status == status)
        if start is not None:
            filters.append(Schedule.scheduled_for >= start)
        if end is not None:
            filters.append(Schedule.scheduled_for < end)
        total = self.session.scalar(select(func.count()).select_from(Schedule).where(*filters)) or 0
        statement = (
            select(Schedule)
            .where(*filters)
            .order_by(Schedule.scheduled_for, Schedule.created_at)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement)), total

    def active_for_post(self, user_id: UUID, post_id: UUID) -> Schedule | None:
        statement = select(Schedule).where(
            Schedule.user_id == user_id,
            Schedule.post_id == post_id,
            Schedule.status.in_([ScheduleStatus.ACTIVE, ScheduleStatus.PAUSED]),
        )
        return self.session.scalar(statement)

    def for_campaign(self, user_id: UUID, campaign_id: UUID) -> list[Schedule]:
        statement = (
            select(Schedule)
            .join(Post, Post.id == Schedule.post_id)
            .where(Schedule.user_id == user_id, Post.campaign_id == campaign_id)
        )
        return list(self.session.scalars(statement))

    def claim_due(self, now: datetime, *, limit: int) -> list[Schedule]:
        statement = (
            select(Schedule)
            .join(Post, Post.id == Schedule.post_id)
            .where(
                Schedule.status == ScheduleStatus.ACTIVE,
                Schedule.next_run_at.is_not(None),
                Schedule.next_run_at <= now,
                Post.status == PostStatus.SCHEDULED,
            )
            .order_by(Schedule.next_run_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        schedules = list(self.session.scalars(statement))
        for schedule in schedules:
            schedule.post.status = PostStatus.PUBLISHING
            schedule.attempt_count += 1
            schedule.last_attempt_at = now
        self.session.commit()
        return schedules

    def claim_stale_publishing(self, cutoff: datetime, *, limit: int) -> list[Schedule]:
        statement = (
            select(Schedule)
            .join(Post, Post.id == Schedule.post_id)
            .where(
                Schedule.status == ScheduleStatus.ACTIVE,
                Schedule.last_attempt_at.is_not(None),
                Schedule.last_attempt_at < cutoff,
                Post.status == PostStatus.PUBLISHING,
            )
            .order_by(Schedule.last_attempt_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(self.session.scalars(statement))
