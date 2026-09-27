from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ScheduleRecurrence, ScheduleStatus

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User


class Schedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "schedules"
    __table_args__ = (
        Index("ix_schedules_due", "status", "next_run_at"),
        Index("ix_schedules_user_post", "user_id", "post_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recurrence: Mapped[ScheduleRecurrence] = mapped_column(
        Enum(ScheduleRecurrence, native_enum=False, length=32),
        default=ScheduleRecurrence.ONCE,
        nullable=False,
    )
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, native_enum=False, length=32),
        default=ScheduleStatus.ACTIVE,
        index=True,
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    recurrence_rule: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    post: Mapped[Post] = relationship(back_populates="schedules")
    user: Mapped[User] = relationship()

    @property
    def retryable(self) -> bool:
        latest = max(
            self.post.publishing_logs,
            key=lambda log: log.attempt_number,
            default=None,
        )
        metadata = latest.response_metadata if latest is not None else None
        return bool(metadata and metadata.get("retry_safe") is True)

    @property
    def outcome_uncertain(self) -> bool:
        latest = max(
            self.post.publishing_logs,
            key=lambda log: log.attempt_number,
            default=None,
        )
        metadata = latest.response_metadata if latest is not None else None
        return bool(metadata and metadata.get("outcome_uncertain") is True)
