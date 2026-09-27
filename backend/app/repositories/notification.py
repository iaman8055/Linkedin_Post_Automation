from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.base import UserOwnedRepository


class NotificationRepository(UserOwnedRepository[Notification]):
    def __init__(self, session: Session) -> None:
        super().__init__(Notification, session)

    def list_recent(self, user_id: UUID, *, offset: int, limit: int) -> list[Notification]:
        return list(self.session.scalars(
            select(Notification).where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        ))

    def unread_count(self, user_id: UUID) -> int:
        return int(self.session.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id, Notification.read_at.is_(None)
            )
        ) or 0)

    def unread(self, user_id: UUID) -> list[Notification]:
        return list(self.session.scalars(select(Notification).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)
        )))
