from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications")


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    user: CurrentUser,
    session: DatabaseSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> NotificationListResponse:
    items, unread = NotificationService(session).list(user.id, offset=offset, limit=limit)
    return NotificationListResponse(items=items, unread_count=unread, offset=offset, limit=limit)


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def unread_count(user: CurrentUser, session: DatabaseSession) -> NotificationUnreadCountResponse:
    count = NotificationService(session).notifications.unread_count(user.id)
    return NotificationUnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID, user: CurrentUser, session: DatabaseSession
) -> NotificationResponse:
    return NotificationResponse.model_validate(
        NotificationService(session).mark_read(user.id, notification_id)
    )


@router.post("/read-all", response_model=NotificationUnreadCountResponse)
def mark_all_read(user: CurrentUser, session: DatabaseSession) -> NotificationUnreadCountResponse:
    NotificationService(session).mark_all_read(user.id)
    return NotificationUnreadCountResponse(unread_count=0)
