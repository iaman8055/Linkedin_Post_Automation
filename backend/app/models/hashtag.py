from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.post import Post


class Hashtag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hashtags"
    __table_args__ = (UniqueConstraint("user_id", "normalized_name", name="uq_hashtag_user_name"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(120), index=True)

    post_links: Mapped[list[PostHashtag]] = relationship(
        back_populates="hashtag", cascade="all, delete-orphan"
    )


class PostHashtag(Base):
    __tablename__ = "post_hashtags"
    __table_args__ = (UniqueConstraint("post_id", "hashtag_id", name="uq_post_hashtag"),)

    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    hashtag_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True
    )

    post: Mapped[Post] = relationship(back_populates="hashtag_links")
    hashtag: Mapped[Hashtag] = relationship(back_populates="post_links")

