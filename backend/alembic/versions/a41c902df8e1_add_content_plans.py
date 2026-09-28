"""add content plans

Revision ID: a41c902df8e1
Revises: 27778c75d2b5
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a41c902df8e1"
down_revision: str | None = "27778c75d2b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "content_ideas",
        sa.Column("category", sa.String(length=64), server_default="educational", nullable=False),
    )
    op.add_column(
        "content_ideas",
        sa.Column("suggested_hook", sa.String(length=300), server_default="", nullable=False),
    )
    op.create_table(
        "content_plans",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("audience", sa.String(length=240), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "APPROVED", name="contentplanstatus", native_enum=False, length=32), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_plans_user_id", "content_plans", ["user_id"])
    op.create_index("ix_content_plans_status", "content_plans", ["status"])
    op.create_table(
        "content_plan_items",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("post_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["content_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_plan_items_plan_id", "content_plan_items", ["plan_id"])
    op.create_index("ix_content_plan_items_post_id", "content_plan_items", ["post_id"])
    op.create_index("ix_content_plan_items_scheduled_for", "content_plan_items", ["scheduled_for"])


def downgrade() -> None:
    op.drop_table("content_plan_items")
    op.drop_table("content_plans")
    op.drop_column("content_ideas", "suggested_hook")
    op.drop_column("content_ideas", "category")
