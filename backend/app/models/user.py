from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.linkedin_account import LinkedInAccount
    from app.models.post import Post
    from app.models.user_settings import UserSettings
    from app.models.writing_profile import WritingProfile


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    settings: Mapped[UserSettings | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    linkedin_accounts: Mapped[list[LinkedInAccount]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    writing_profiles: Mapped[list[WritingProfile]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    campaigns: Mapped[list[Campaign]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[list[Post]] = relationship(back_populates="user", cascade="all, delete-orphan")

