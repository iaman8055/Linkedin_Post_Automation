from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PostStatus


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecentPostsArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=50)
    status: PostStatus | None = None


class LimitedArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=50)


class CalendarArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: datetime
    end: datetime


class CreateDraftArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=240)
    content: str = Field(min_length=1, max_length=3000)
    language: str = Field(default="English", min_length=2, max_length=32)


ToolName = Literal[
    "get_recent_posts",
    "get_top_posts",
    "get_writing_profile",
    "get_content_ideas",
    "get_content_plans",
    "get_knowledge",
    "get_calendar",
    "create_draft",
]
