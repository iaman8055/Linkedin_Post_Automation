from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AICopilotConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_copilot_conversations"
    __table_args__ = (
        Index("ix_copilot_conversations_workspace_updated", "workspace_id", "updated_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    messages: Mapped[list[AICopilotMessage]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="AICopilotMessage.created_at",
    )


class AICopilotMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_copilot_messages"
    __table_args__ = (
        Index("ix_copilot_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_copilot_conversations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(String(300))
    conversation: Mapped[AICopilotConversation] = relationship(back_populates="messages")


class AICopilotAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_copilot_actions"
    __table_args__ = (
        Index("ix_copilot_actions_workspace_status", "workspace_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_copilot_conversations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    message_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("ai_copilot_messages.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="PENDING", index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[dict[str, Any] | list[dict[str, Any]] | None] = mapped_column(JSON)
