from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CommentSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style: Literal["professional", "friendly", "concise", "thoughtful", "humorous"]
    response: str = Field(min_length=2, max_length=1250)


class CommentSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suggestions: list[CommentSuggestion] = Field(min_length=5, max_length=5)


class GenerateCommentResponsesRequest(BaseModel):
    comment: str = Field(min_length=2, max_length=1250)
    post_context: str | None = Field(default=None, max_length=3000)


class GenerateCommentResponsesResponse(BaseModel):
    job_id: UUID
    suggestions: list[CommentSuggestion]
    disclaimer: str


class ExperimentVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: Literal["A", "B"]
    title: str = Field(min_length=2, max_length=240)
    content: str = Field(min_length=10, max_length=3000)
    change_summary: str = Field(min_length=2, max_length=500)


class ExperimentVersions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    versions: list[ExperimentVersion] = Field(min_length=2, max_length=2)


class CreateExperimentRequest(BaseModel):
    source_post_id: UUID
    name: str = Field(min_length=2, max_length=160)
    hypothesis: str | None = Field(default=None, max_length=1000)
    comparison_axis: Literal["hook", "cta", "structure", "tone", "length"]


class ExperimentPostResponse(BaseModel):
    id: UUID
    title: str | None
    content: str
    status: str


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    hypothesis: str | None
    comparison_axis: str
    version_a: ExperimentPostResponse
    version_b: ExperimentPostResponse
    created_at: datetime


class ExperimentMetric(BaseModel):
    post_id: UUID
    impressions: int | None
    reactions: int | None
    comments: int | None
    shares: int | None
    engagement_rate: float | None


class ExperimentComparisonResponse(BaseModel):
    experiment_id: UUID
    status: Literal["awaiting_publication", "awaiting_analytics", "ready"]
    version_a: ExperimentMetric | None
    version_b: ExperimentMetric | None
    better_version: Literal["A", "B"] | None
    explanation: str
