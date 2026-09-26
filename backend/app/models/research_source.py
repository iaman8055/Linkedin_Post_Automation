from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.post import Post


class ResearchSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_sources"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    relevant_content: Mapped[str | None] = mapped_column(Text)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    post_links: Mapped[list[PostResearchSource]] = relationship(
        back_populates="research_source", cascade="all, delete-orphan"
    )


class PostResearchSource(Base):
    __tablename__ = "post_research_sources"
    __table_args__ = (
        UniqueConstraint("post_id", "research_source_id", name="uq_post_research_source"),
    )

    post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    research_source_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("research_sources.id", ondelete="CASCADE"), primary_key=True
    )

    post: Mapped[Post] = relationship(back_populates="research_source_links")
    research_source: Mapped[ResearchSource] = relationship(back_populates="post_links")

