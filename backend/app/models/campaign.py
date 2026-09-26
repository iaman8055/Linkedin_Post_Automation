from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ApprovalMode, CampaignStatus

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User
    from app.models.writing_profile import WritingProfile


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    writing_profile_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("writing_profiles.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    topic: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_days: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, native_enum=False, length=32),
        default=CampaignStatus.DRAFT,
        index=True,
        nullable=False,
    )
    approval_mode: Mapped[ApprovalMode] = mapped_column(
        Enum(ApprovalMode, native_enum=False, length=32),
        default=ApprovalMode.MANUAL,
        nullable=False,
    )
    default_posting_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    content_strategy: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="campaigns")
    writing_profile: Mapped[WritingProfile | None] = relationship(back_populates="campaigns")
    posts: Mapped[list[Post]] = relationship(back_populates="campaign")

