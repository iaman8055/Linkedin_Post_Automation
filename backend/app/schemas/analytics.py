from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticsStatusResponse(BaseModel):
    connected: bool
    permission_granted: bool
    required_scope: str
    collection_available: bool


class PostAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    impressions: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    engagement_rate: float | None
    captured_at: datetime


class AnalyticsPostItem(BaseModel):
    post_id: UUID
    title: str | None
    content_excerpt: str
    published_at: datetime | None
    analytics: PostAnalyticsResponse


class AnalyticsOverviewResponse(BaseModel):
    posts: list[AnalyticsPostItem]
    total_impressions: int | None
    total_likes: int | None
    total_comments: int | None
    total_shares: int | None
    average_engagement_rate: float | None


class PerformanceInsight(BaseModel):
    type: str
    title: str
    observation: str
    evidence: str
    sample_size: int


class PerformanceInsightsResponse(BaseModel):
    status: str
    analyzed_posts: int
    minimum_required: int
    disclaimer: str
    insights: list[PerformanceInsight]
