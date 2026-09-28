from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ContentPlanStatus, IdeaStatus, PostStatus

IdeaCategory = Literal[
    "educational", "storytelling", "technical", "career", "personal",
    "industry", "opinion", "case_study",
]
RepurposeFormat = Literal[
    "linkedin_post", "linkedin_carousel", "linkedin_short_post",
    "linkedin_long_form", "x_thread", "newsletter", "video_script",
]
PostingFrequency = Literal["2_per_week", "3_per_week", "5_per_week", "daily"]


class GeneratedIdea(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=240)
    topic: str = Field(min_length=2, max_length=160)
    category: IdeaCategory
    angle: str = Field(min_length=3, max_length=240)
    description: str = Field(min_length=5, max_length=1000)
    suggested_hook: str = Field(min_length=5, max_length=300)
    suggested_format: str = Field(min_length=2, max_length=80)


class GeneratedIdeas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ideas: list[GeneratedIdea] = Field(min_length=1, max_length=10)


class GenerateIdeasRequest(BaseModel):
    topics: list[str] = Field(min_length=1, max_length=10)
    audience: str | None = Field(default=None, max_length=240)
    count: int = Field(default=10, ge=1, le=10)
    use_personal_context: bool = False

    @field_validator("topics")
    @classmethod
    def normalize_topics(cls, value: list[str]) -> list[str]:
        result = [item.strip() for item in value if item.strip()]
        if not result:
            raise ValueError("at least one topic is required")
        return result


class GenerateIdeasResponse(BaseModel):
    job_id: UUID
    ideas: list[GeneratedIdea]


class ContentIdeaCreate(GeneratedIdea):
    pass


class ContentIdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    topic: str
    category: str
    angle: str
    description: str
    suggested_hook: str
    suggested_format: str
    status: IdeaStatus
    created_at: datetime


class ContentIdeaListResponse(BaseModel):
    items: list[ContentIdeaResponse]
    total: int


class RepurposeRequest(BaseModel):
    source_type: Literal["paste_text", "blog_article", "linkedin_post", "notes", "url"]
    source_content: str = Field(min_length=30, max_length=30_000)
    output_format: RepurposeFormat = "linkedin_post"
    count: int = Field(default=1, ge=1, le=10)
    audience: str | None = Field(default=None, max_length=240)
    tone: str = Field(default="Conversational", max_length=80)


class RepurposedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3, max_length=240)
    content: str = Field(min_length=10, max_length=5000)
    angle: str = Field(min_length=3, max_length=240)


class RepurposedItems(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[RepurposedItem] = Field(min_length=1, max_length=10)


class RepurposedPostResponse(BaseModel):
    id: UUID
    title: str | None
    content: str
    status: PostStatus


class RepurposeResponse(BaseModel):
    job_id: UUID
    posts: list[RepurposedPostResponse]


class PlannedContentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=2, max_length=160)
    post_type: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=3, max_length=240)
    content: str = Field(min_length=10, max_length=3000)


class PlannedContentItems(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[PlannedContentItem] = Field(min_length=1, max_length=30)


class GenerateContentPlanRequest(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    frequency: PostingFrequency
    duration_days: Literal[7, 14, 30]
    topics: list[str] = Field(min_length=1, max_length=10)
    audience: str = Field(min_length=2, max_length=240)
    start_date: date
    posting_time: time
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class ContentPlanItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    position: int
    topic: str
    post_type: str
    title: str
    content: str
    scheduled_for: datetime
    post_id: UUID | None


class ContentPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    audience: str
    timezone: str
    status: ContentPlanStatus
    items: list[ContentPlanItemResponse]
    created_at: datetime


class ContentPlanListResponse(BaseModel):
    items: list[ContentPlanResponse]


class ApproveContentPlanRequest(BaseModel):
    schedule_for_auto_publish: bool = False


class ApproveContentPlanResponse(BaseModel):
    plan: ContentPlanResponse
    created_post_ids: list[UUID]
    scheduled_count: int
