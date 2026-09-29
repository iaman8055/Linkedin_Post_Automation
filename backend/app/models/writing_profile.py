from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorkspaceOwnedMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.user import User


class WritingProfile(UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceOwnedMixin, Base):
    __tablename__ = "writing_profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    tone: Mapped[str | None] = mapped_column(String(80))
    sentence_style: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str] = mapped_column(String(32), default="English", nullable=False)
    emoji_preference: Mapped[str | None] = mapped_column(String(32))
    paragraph_length: Mapped[str | None] = mapped_column(String(32))
    technical_depth: Mapped[str | None] = mapped_column(String(32))
    cta_preference: Mapped[str | None] = mapped_column(Text)
    preferred_vocabulary: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    additional_guidance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="writing_profiles")
    campaigns: Mapped[list[Campaign]] = relationship(back_populates="writing_profile")
