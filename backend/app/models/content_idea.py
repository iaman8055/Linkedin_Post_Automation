from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import IdeaStatus


class ContentIdea(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_ideas"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    topic: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="educational")
    angle: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_hook: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    suggested_format: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[IdeaStatus] = mapped_column(
        Enum(IdeaStatus, native_enum=False, length=32),
        default=IdeaStatus.NEW,
        index=True,
        nullable=False,
    )
