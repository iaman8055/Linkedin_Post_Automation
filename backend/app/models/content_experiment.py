from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.post import Post


class ContentExperiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_experiments"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text)
    comparison_axis: Mapped[str] = mapped_column(String(32), nullable=False)
    version_a_post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_b_post_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("posts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_a: Mapped[Post] = relationship(foreign_keys=[version_a_post_id])
    version_b: Mapped[Post] = relationship(foreign_keys=[version_b_post_id])
