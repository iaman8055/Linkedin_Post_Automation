import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TemplateStatus
from app.schemas.post import normalize_required_text, normalize_updated_text


def validate_settings(value: dict[str, Any]) -> dict[str, Any]:
    if len(json.dumps(value)) > 10_000:
        raise ValueError("must be 10 KB or smaller")
    return value


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    body: str = Field(min_length=1, max_length=10_000)
    settings: dict[str, Any] = Field(default_factory=dict)

    _normalize_name = field_validator("name")(normalize_required_text)
    _normalize_body = field_validator("body")(normalize_required_text)
    _validate_settings = field_validator("settings")(validate_settings)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    body: str | None = Field(default=None, min_length=1, max_length=10_000)
    settings: dict[str, Any] | None = None

    _normalize_name = field_validator("name")(normalize_updated_text)
    _normalize_body = field_validator("body")(normalize_updated_text)

    @field_validator("settings")
    @classmethod
    def updated_settings(cls, value: dict[str, Any] | None) -> dict[str, Any]:
        if value is None:
            raise ValueError("must not be null")
        return validate_settings(value)


class TemplateRenderRequest(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)

    @field_validator("values")
    @classmethod
    def valid_values(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 50:
            raise ValueError("must contain 50 values or fewer")
        if any(len(item) > 3000 for item in value.values()):
            raise ValueError("each value must be 3,000 characters or fewer")
        return value


class TemplateRenderResponse(BaseModel):
    content: str


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    body: str
    placeholders: list[str]
    settings: dict[str, Any]
    status: TemplateStatus
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int
    offset: int
    limit: int
