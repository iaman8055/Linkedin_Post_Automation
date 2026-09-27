from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.post import PostResponse, normalize_required_text


class AIProviderStatusResponse(BaseModel):
    selected_provider: str | None
    selected_model: str | None
    provider_installed: bool
    registered_providers: list[str]


class GeneratePostsRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    subject: str = Field(min_length=2, max_length=240)
    audience: str = Field(min_length=2, max_length=240)
    tone: str = Field(default="professional and conversational", min_length=2, max_length=120)
    language: str = Field(default="English", min_length=2, max_length=32)
    length: Literal["short", "medium", "long"] = "medium"
    call_to_action: str | None = Field(default=None, max_length=240)
    include_hashtags: bool = True
    hashtag_count: int = Field(default=3, ge=0, le=8)
    number_of_posts: int = Field(default=1, ge=1, le=10)

    _normalize_topic = field_validator("topic")(normalize_required_text)
    _normalize_subject = field_validator("subject")(normalize_required_text)
    _normalize_audience = field_validator("audience")(normalize_required_text)
    _normalize_tone = field_validator("tone")(normalize_required_text)
    _normalize_language = field_validator("language")(normalize_required_text)


class GeneratedDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=240)
    angle: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=2800)
    hashtags: list[str] = Field(max_length=8)


class GeneratedDraftCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posts: list[GeneratedDraft] = Field(min_length=1, max_length=10)


class GeneratePostsResponse(BaseModel):
    job_id: UUID
    posts: list[PostResponse]
