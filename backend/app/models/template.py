from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, WorkspaceOwnedMixin
from app.models.enums import TemplateStatus


class Template(UUIDPrimaryKeyMixin, TimestampMixin, WorkspaceOwnedMixin, Base):
    __tablename__ = "templates"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    placeholders: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[TemplateStatus] = mapped_column(
        Enum(TemplateStatus, native_enum=False, length=32),
        default=TemplateStatus.ACTIVE,
        index=True,
        nullable=False,
    )
