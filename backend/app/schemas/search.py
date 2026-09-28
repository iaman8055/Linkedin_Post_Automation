from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

SearchEntityType = Literal["post", "idea", "knowledge", "template"]


class GlobalSearchFilters(BaseModel):
    query: str | None = Field(default=None, max_length=200)
    entity_type: Literal["all", "post", "idea", "knowledge", "template"] = "all"
    status: str | None = Field(default=None, max_length=32)
    topic: str | None = Field(default=None, max_length=160)
    tag: str | None = Field(default=None, max_length=80)
    date_from: date | None = None
    date_to: date | None = None
    limit: int = Field(default=50, ge=1, le=100)


class GlobalSearchResult(BaseModel):
    id: UUID
    entity_type: SearchEntityType
    title: str
    excerpt: str
    status: str | None
    topic: str | None
    tags: list[str]
    updated_at: datetime
    scheduled_for: datetime | None = None
    url: str


class GlobalSearchResponse(BaseModel):
    items: list[GlobalSearchResult]
    total: int
    query: str | None
