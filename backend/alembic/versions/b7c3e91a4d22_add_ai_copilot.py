"""add AI Copilot conversations and confirmed actions

Revision ID: b7c3e91a4d22
Revises: 9d8a2c4e6f10
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c3e91a4d22"
down_revision: str | None = "9d8a2c4e6f10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_copilot_conversations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_copilot_conversations_user_id", "ai_copilot_conversations", ["user_id"]
    )
    op.create_index(
        "ix_ai_copilot_conversations_workspace_id",
        "ai_copilot_conversations", ["workspace_id"],
    )
    op.create_index(
        "ix_ai_copilot_conversations_last_message_at",
        "ai_copilot_conversations", ["last_message_at"],
    )
    op.create_index(
        "ix_copilot_conversations_workspace_updated",
        "ai_copilot_conversations", ["workspace_id", "updated_at"],
    )

    op.create_table(
        "ai_copilot_messages",
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("suggested_action", sa.String(length=300)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["ai_copilot_conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_copilot_messages_conversation_id",
        "ai_copilot_messages", ["conversation_id"],
    )
    op.create_index(
        "ix_copilot_messages_conversation_created",
        "ai_copilot_messages", ["conversation_id", "created_at"],
    )

    op.create_table(
        "ai_copilot_actions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=80), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("result", sa.JSON()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["ai_copilot_conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["ai_copilot_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    indexed_columns = (
        "user_id", "workspace_id", "conversation_id", "message_id", "status", "expires_at"
    )
    for column in indexed_columns:
        op.create_index(f"ix_ai_copilot_actions_{column}", "ai_copilot_actions", [column])
    op.create_index(
        "ix_copilot_actions_workspace_status",
        "ai_copilot_actions", ["workspace_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("ai_copilot_actions")
    op.drop_table("ai_copilot_messages")
    op.drop_table("ai_copilot_conversations")
