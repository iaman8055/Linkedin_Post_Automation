from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QualityStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class QualitySeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=64)
    severity: QualitySeverity
    message: str = Field(min_length=1, max_length=500)
    suggestion: str = Field(min_length=1, max_length=500)


class AIQualityIssues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[QualityIssue] = Field(max_length=20)


class QualityCheckResponse(BaseModel):
    post_id: UUID
    status: QualityStatus
    issues: list[QualityIssue]
    ai_review_performed: bool
    job_id: UUID | None = None
