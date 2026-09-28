from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

KnowledgeCategory = Literal[
    "project", "resume", "skill", "experience", "article", "note",
    "previous_content", "achievement", "technical_knowledge",
]


class KnowledgeItemBase(BaseModel):
    category: KnowledgeCategory
    title: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=10_000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    is_private: bool = True

    @field_validator("title", "content")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must contain non-whitespace characters")
        return normalized


class KnowledgeItemCreate(KnowledgeItemBase):
    pass


class KnowledgeItemUpdate(BaseModel):
    category: KnowledgeCategory | None = None
    title: str | None = Field(default=None, min_length=1, max_length=240)
    content: str | None = Field(default=None, min_length=1, max_length=10_000)
    tags: list[str] | None = Field(default=None, max_length=20)
    is_private: bool | None = None

    @field_validator("title", "content")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("must contain non-whitespace characters")
        return normalized


class KnowledgeItemResponse(KnowledgeItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class KnowledgeItemListResponse(BaseModel):
    items: list[KnowledgeItemResponse]
    total: int
