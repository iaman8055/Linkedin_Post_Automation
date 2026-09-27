from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import MediaType


class PostMediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    media_type: MediaType
    mime_type: str
    size_bytes: int | None
    position: int
    metadata_json: dict[str, object]
    created_at: datetime


class PostMediaListResponse(BaseModel):
    items: list[PostMediaResponse]
