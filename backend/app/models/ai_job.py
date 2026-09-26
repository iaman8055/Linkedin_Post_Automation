from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AIJobStatus


class AIJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_jobs"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    status: Mapped[AIJobStatus] = mapped_column(
        Enum(AIJobStatus, native_enum=False, length=32),
        default=AIJobStatus.PENDING,
        index=True,
        nullable=False,
    )
    provider: Mapped[str | None] = mapped_column(String(80))
    provider_job_id: Mapped[str | None] = mapped_column(String(255), index=True)
    input_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)

