from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorkspaceOwnedMixin
from app.models.enums import PostStatus

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.hashtag import PostHashtag
    from app.models.post_analytics import PostAnalytics
    from app.models.post_media import PostMedia
    from app.models.publishing_log import PublishingLog
    from app.models.research_source import PostResearchSource
    from app.models.schedule import Schedule
    from app.models.user import User


class Post(UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceOwnedMixin, Base):
    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_user_status_created", "user_id", "status", "created_at"),
        Index("ix_posts_workspace_status_created", "workspace_id", "status", "created_at"),
        Index("ix_posts_user_campaign", "user_id", "campaign_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("campaigns.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="English", nullable=False)
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, native_enum=False, length=32),
        default=PostStatus.DRAFT,
        index=True,
        nullable=False,
    )
    linkedin_post_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content_fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)

    user: Mapped[User] = relationship(back_populates="posts")
    campaign: Mapped[Campaign | None] = relationship(back_populates="posts")
    schedules: Mapped[list[Schedule]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    media: Mapped[list[PostMedia]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    publishing_logs: Mapped[list[PublishingLog]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    analytics: Mapped[list[PostAnalytics]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    hashtag_links: Mapped[list[PostHashtag]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    research_source_links: Mapped[list[PostResearchSource]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
