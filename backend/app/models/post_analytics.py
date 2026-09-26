from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.post import Post


class PostAnalytics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "post_analytics"
    __table_args__ = (Index("ix_post_analytics_post_captured", "post_id", "captured_at"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    impressions: Mapped[int | None] = mapped_column(Integer)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    shares: Mapped[int | None] = mapped_column(Integer)
    engagement_rate: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    post: Mapped[Post] = relationship(back_populates="analytics")

