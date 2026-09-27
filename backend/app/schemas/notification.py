from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    title: str
    message: str
    read_at: datetime | None
    data: dict[str, Any]
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(gt=0)


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int = Field(ge=0)
