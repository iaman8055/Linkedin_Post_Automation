from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PostStatus


def normalize_required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("must contain non-whitespace characters")
    return normalized


def normalize_updated_text(value: str | None) -> str:
    if value is None:
        raise ValueError("must not be null")
    return normalize_required_text(value)


class PostCreate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    content: str = Field(min_length=1, max_length=3000)
    language: str = Field(default="English", min_length=2, max_length=32)

    _normalize_content = field_validator("content")(normalize_required_text)
    _normalize_language = field_validator("language")(normalize_required_text)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    content: str | None = Field(default=None, min_length=1, max_length=3000)
    language: str | None = Field(default=None, min_length=2, max_length=32)

    _normalize_content = field_validator("content")(normalize_updated_text)
    _normalize_language = field_validator("language")(normalize_updated_text)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID | None
    title: str | None
    content: str
    language: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    published_at: datetime | None


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    offset: int
    limit: int
