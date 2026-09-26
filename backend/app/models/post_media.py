from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MediaType

if TYPE_CHECKING:
    from app.models.post import Post


class PostMedia(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "post_media"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, native_enum=False, length=32), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    public_url: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    post: Mapped[Post] = relationship(back_populates="media")

