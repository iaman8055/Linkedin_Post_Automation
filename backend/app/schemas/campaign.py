import json
from datetime import datetime, time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ApprovalMode, CampaignStatus
from app.schemas.post import normalize_required_text


def validate_timezone(value: str) -> str:
    normalized = normalize_required_text(value)
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("must be a valid IANA timezone") from exc
    return normalized


def normalize_updated_text(value: str | None) -> str:
    if value is None:
        raise ValueError("must not be null")
    return normalize_required_text(value)


def validate_updated_timezone(value: str | None) -> str:
    if value is None:
        raise ValueError("must not be null")
    return validate_timezone(value)


def validate_strategy(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is not None and len(json.dumps(value)) > 50_000:
        raise ValueError("must be 50 KB or smaller")
    return value


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    topic: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    duration_days: int | None = Field(default=None, ge=1, le=3650)
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    default_posting_time: time | None = None
    timezone: str = Field(default="UTC", max_length=64)
    writing_profile_id: UUID | None = None
    content_strategy: dict[str, Any] | None = None

    _normalize_name = field_validator("name")(normalize_required_text)
    _normalize_topic = field_validator("topic")(normalize_required_text)
    _validate_timezone = field_validator("timezone")(validate_timezone)
    _validate_strategy = field_validator("content_strategy")(validate_strategy)


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    topic: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    duration_days: int | None = Field(default=None, ge=1, le=3650)
    approval_mode: ApprovalMode | None = None
    default_posting_time: time | None = None
    timezone: str | None = Field(default=None, max_length=64)
    writing_profile_id: UUID | None = None
    content_strategy: dict[str, Any] | None = None

    _normalize_name = field_validator("name")(normalize_updated_text)
    _normalize_topic = field_validator("topic")(normalize_updated_text)
    _validate_timezone = field_validator("timezone")(validate_updated_timezone)
    _validate_strategy = field_validator("content_strategy")(validate_strategy)

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            required = {"name", "topic", "approval_mode", "timezone"}
            if any(field in data and data[field] is None for field in required):
                raise ValueError("required campaign fields must not be null")
        return data


class CampaignTransitionRequest(BaseModel):
    status: CampaignStatus


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    topic: str
    description: str | None
    duration_days: int | None
    status: CampaignStatus
    approval_mode: ApprovalMode
    default_posting_time: time | None
    timezone: str
    writing_profile_id: UUID | None
    content_strategy: dict[str, Any] | None
    post_count: int
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    total: int
    offset: int
    limit: int
