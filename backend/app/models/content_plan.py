from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorkspaceOwnedMixin
from app.models.enums import ContentPlanStatus

if TYPE_CHECKING:
    from app.models.post import Post


class ContentPlan(UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceOwnedMixin, Base):
    __tablename__ = "content_plans"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    audience: Mapped[str] = mapped_column(String(240), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ContentPlanStatus] = mapped_column(
        Enum(ContentPlanStatus, native_enum=False, length=32),
        default=ContentPlanStatus.DRAFT,
        index=True,
        nullable=False,
    )
    items: Mapped[list[ContentPlanItem]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="ContentPlanItem.scheduled_for",
    )


class ContentPlanItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_plan_items"

    plan_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("content_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str] = mapped_column(String(160), nullable=False)
    post_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    post_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="SET NULL"), index=True
    )
    plan: Mapped[ContentPlan] = relationship(back_populates="items")
    post: Mapped[Post | None] = relationship()
