from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PublishingStatus

if TYPE_CHECKING:
    from app.models.post import Post


class PublishingLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publishing_logs"
    __table_args__ = (
        Index("ix_publishing_logs_post_attempt", "post_id", "attempt_number"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[PublishingStatus] = mapped_column(
        Enum(PublishingStatus, native_enum=False, length=32), index=True, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    external_post_id: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    response_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    post: Mapped[Post] = relationship(back_populates="publishing_logs")

