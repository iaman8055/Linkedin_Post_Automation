from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.post import normalize_required_text


class WritingProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    tone: str | None = Field(default=None, max_length=80)
    sentence_style: str | None = Field(default=None, max_length=80)
    language: str = Field(default="English", min_length=2, max_length=32)
    emoji_preference: str | None = Field(default=None, max_length=32)
    paragraph_length: str | None = Field(default=None, max_length=32)
    technical_depth: str | None = Field(default=None, max_length=32)
    cta_preference: str | None = Field(default=None, max_length=500)
    preferred_vocabulary: list[str] = Field(default_factory=list, max_length=30)
    additional_guidance: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

    _normalize_name = field_validator("name")(normalize_required_text)
    _normalize_language = field_validator("language")(normalize_required_text)

    @field_validator("preferred_vocabulary")
    @classmethod
    def normalize_vocabulary(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            word = value.strip()
            if not word or len(word) > 80:
                continue
            key = word.casefold()
            if key not in seen:
                seen.add(key)
                normalized.append(word)
        return normalized


class WritingProfileCreate(WritingProfileBase):
    pass


class WritingProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    tone: str | None = Field(default=None, max_length=80)
    sentence_style: str | None = Field(default=None, max_length=80)
    language: str | None = Field(default=None, min_length=2, max_length=32)
    emoji_preference: str | None = Field(default=None, max_length=32)
    paragraph_length: str | None = Field(default=None, max_length=32)
    technical_depth: str | None = Field(default=None, max_length=32)
    cta_preference: str | None = Field(default=None, max_length=500)
    preferred_vocabulary: list[str] | None = Field(default=None, max_length=30)
    additional_guidance: dict[str, Any] | None = None
    is_default: bool | None = None

    _normalize_name = field_validator("name")(normalize_required_text)
    _normalize_language = field_validator("language")(normalize_required_text)


class WritingProfileResponse(WritingProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class WritingProfileListResponse(BaseModel):
    items: list[WritingProfileResponse]
    total: int


class AnalyzeWritingStyleRequest(BaseModel):
    post_ids: list[UUID] = Field(default_factory=list, max_length=30)


class WritingStyleAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    average_sentence_length: float = Field(ge=1, le=100)
    paragraph_length: Literal["Short", "Medium", "Long"]
    formality: Literal["Casual", "Conversational", "Professional", "Formal"]
    tone: str = Field(min_length=2, max_length=80)
    emoji_frequency: Literal["None", "Low", "Medium", "High"]
    hashtag_frequency: Literal["None", "Low", "Medium", "High"]
    storytelling: Literal["Low", "Medium", "High"]
    technical_depth: Literal["Accessible", "Balanced", "Expert"]
    cta_style: str = Field(min_length=2, max_length=240)
    opening_style: str = Field(min_length=2, max_length=240)
    vocabulary_patterns: list[str] = Field(max_length=20)


class AnalyzeWritingStyleResponse(BaseModel):
    job_id: UUID
    sample_size: int
    disclaimer: str
    analysis: WritingStyleAnalysis
    suggested_profile: WritingProfileCreate
