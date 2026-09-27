from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import ScheduleRecurrence, ScheduleStatus


def validate_schedule_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("must be a valid IANA timezone") from exc
    return value


def validate_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("must include a UTC offset")
    return value


class ScheduleCreate(BaseModel):
    post_id: UUID
    scheduled_for: datetime
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    recurrence: ScheduleRecurrence = ScheduleRecurrence.ONCE
    weekdays: list[int] | None = None
    custom_dates: list[datetime] | None = None

    _valid_timezone = field_validator("timezone")(validate_schedule_timezone)
    _timezone_aware = field_validator("scheduled_for")(validate_aware_datetime)

    @field_validator("weekdays")
    @classmethod
    def valid_weekdays(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        normalized = sorted(set(value))
        if not normalized or any(day < 0 or day > 6 for day in normalized):
            raise ValueError("must contain weekday numbers from 0 (Monday) to 6 (Sunday)")
        return normalized

    @field_validator("custom_dates")
    @classmethod
    def aware_custom_dates(cls, value: list[datetime] | None) -> list[datetime] | None:
        if value is None:
            return None
        if not value or any(item.tzinfo is None or item.utcoffset() is None for item in value):
            raise ValueError("must contain timezone-aware dates")
        return sorted(set(value))

    @model_validator(mode="after")
    def recurrence_details_match(self) -> "ScheduleCreate":
        if self.recurrence == ScheduleRecurrence.WEEKLY and not self.weekdays:
            raise ValueError("weekdays are required for weekly schedules")
        if self.recurrence == ScheduleRecurrence.CUSTOM and not self.custom_dates:
            raise ValueError("custom_dates are required for custom schedules")
        if self.recurrence != ScheduleRecurrence.WEEKLY and self.weekdays is not None:
            raise ValueError("weekdays are only valid for weekly schedules")
        if self.recurrence != ScheduleRecurrence.CUSTOM and self.custom_dates is not None:
            raise ValueError("custom_dates are only valid for custom schedules")
        return self

    def recurrence_details(self) -> dict[str, Any] | None:
        if self.recurrence == ScheduleRecurrence.WEEKLY:
            return {"weekdays": self.weekdays}
        if self.recurrence == ScheduleRecurrence.CUSTOM:
            return {"custom_dates": [item.isoformat() for item in self.custom_dates or []]}
        return None


class ScheduleUpdate(BaseModel):
    scheduled_for: datetime
    timezone: str = Field(min_length=1, max_length=64)

    _valid_timezone = field_validator("timezone")(validate_schedule_timezone)
    _timezone_aware = field_validator("scheduled_for")(validate_aware_datetime)


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    recurrence: ScheduleRecurrence
    status: ScheduleStatus
    timezone: str
    scheduled_for: datetime
    next_run_at: datetime | None
    recurrence_rule: dict[str, Any] | None
    attempt_count: int
    last_attempt_at: datetime | None
    retryable: bool
    outcome_uncertain: bool
    created_at: datetime
    updated_at: datetime


class ScheduleListResponse(BaseModel):
    items: list[ScheduleResponse]
    total: int
    offset: int
    limit: int
