from datetime import datetime

from pydantic import BaseModel, Field


class AchievementResponse(BaseModel):
    code: str
    title: str
    description: str
    unlocked_at: datetime


class CreatorProgressResponse(BaseModel):
    creator_level: int
    level_points: int
    next_level_points: int
    posts_published: int
    drafts_created: int
    ideas_generated: int
    total_impressions: int | None
    current_streak: int
    monthly_post_target: int
    monthly_posts_published: int
    monthly_goal_percent: int
    achievements: list[AchievementResponse]


class CreatorGoalUpdate(BaseModel):
    monthly_post_target: int = Field(ge=1, le=100)
