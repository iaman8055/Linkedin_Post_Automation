from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post_analytics import PostAnalytics
from app.repositories.base import UserOwnedRepository


class PostAnalyticsRepository(UserOwnedRepository[PostAnalytics]):
    def __init__(self, session: Session) -> None:
        super().__init__(PostAnalytics, session)

    def latest_for_user(self, user_id: UUID) -> list[PostAnalytics]:
        latest = (
            select(
                PostAnalytics.post_id,
                func.max(PostAnalytics.captured_at).label("captured_at"),
            )
            .where(PostAnalytics.user_id == user_id)
            .group_by(PostAnalytics.post_id)
            .subquery()
        )
        statement = (
            select(PostAnalytics)
            .join(
                latest,
                (PostAnalytics.post_id == latest.c.post_id)
                & (PostAnalytics.captured_at == latest.c.captured_at),
            )
            .where(PostAnalytics.user_id == user_id)
            .order_by(PostAnalytics.captured_at.desc())
        )
        return list(self.session.scalars(statement))

    def history_for_post(
        self, user_id: UUID, post_id: UUID, *, limit: int
    ) -> list[PostAnalytics]:
        return list(self.session.scalars(
            select(PostAnalytics).where(
                PostAnalytics.user_id == user_id,
                PostAnalytics.post_id == post_id,
            ).order_by(PostAnalytics.captured_at.desc()).limit(limit)
        ))
