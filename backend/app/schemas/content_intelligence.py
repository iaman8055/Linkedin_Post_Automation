from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ScoreDimension = Literal[
    "hook", "clarity", "readability", "engagement_potential", "storytelling",
    "value", "cta", "structure", "authenticity",
]
HookCategory = Literal[
    "curiosity", "contrarian", "story", "question", "data_driven",
    "personal_experience", "mistake", "lesson", "bold_statement",
]


class ScoreBreakdownItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: ScoreDimension
    score: int = Field(ge=0, le=100)
    explanation: str = Field(min_length=1, max_length=500)


class AIPostScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    breakdown: list[ScoreBreakdownItem] = Field(min_length=9, max_length=9)


class PostScoreResponse(AIPostScore):
    post_id: UUID
    job_id: UUID
    disclaimer: str


class GenerateHooksRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=240)
    count: int = Field(default=7, ge=5, le=10)


class GeneratedHook(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: HookCategory
    text: str = Field(min_length=5, max_length=300)


class AIGeneratedHooks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hooks: list[GeneratedHook] = Field(min_length=5, max_length=10)


class GenerateHooksResponse(BaseModel):
    job_id: UUID
    hooks: list[GeneratedHook]
