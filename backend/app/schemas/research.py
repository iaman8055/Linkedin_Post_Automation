from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.post import normalize_required_text


class ResearchSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    topic: Literal["general", "news"] = "general"
    max_results: int = Field(default=5, ge=1, le=10)
    time_range: Literal["day", "week", "month", "year"] | None = None

    _normalize_query = field_validator("query")(normalize_required_text)


class ResearchSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    title: str
    retrieved_at: datetime
    summary: str | None
    relevant_content: str | None
    source_metadata: dict[str, object]


class ResearchSearchResponse(BaseModel):
    answer: str | None
    provider: str
    sources: list[ResearchSourceResponse]


class ResearchSourceListResponse(BaseModel):
    items: list[ResearchSourceResponse]
    total: int
    offset: int
    limit: int


class ResearchProviderStatusResponse(BaseModel):
    selected_provider: str | None
    configured: bool
