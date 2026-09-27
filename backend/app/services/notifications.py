from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.notifications = NotificationRepository(session)

    def create(
        self, user_id: UUID, *, event_type: str, title: str, message: str,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        return self.notifications.create_for_user(
            user_id, event_type=event_type, title=title, message=message, data=data or {}
        )

    def list(self, user_id: UUID, *, offset: int, limit: int) -> tuple[list[Notification], int]:
        return (
            self.notifications.list_recent(user_id, offset=offset, limit=limit),
            self.notifications.unread_count(user_id),
        )

    def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification:
        notification = self.notifications.get_for_user(notification_id, user_id)
        if notification is None:
            raise ApplicationError("NOTIFICATION_NOT_FOUND", "Notification not found.", 404)
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(notification)
        return notification

    def mark_all_read(self, user_id: UUID) -> int:
        items = self.notifications.unread(user_id)
        now = datetime.now(UTC)
        for item in items:
            item.read_at = now
        self.session.commit()
        return len(items)
