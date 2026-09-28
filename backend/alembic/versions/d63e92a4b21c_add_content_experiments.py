"""add content experiments

Revision ID: d63e92a4b21c
Revises: c52d81f3a10b
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d63e92a4b21c"
down_revision: str | None = "c52d81f3a10b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_experiments",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("comparison_axis", sa.String(length=32), nullable=False),
        sa.Column("version_a_post_id", sa.Uuid(), nullable=False),
        sa.Column("version_b_post_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_a_post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_b_post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_experiments_user_id", "content_experiments", ["user_id"])
    op.create_index(
        "ix_content_experiments_version_a_post_id", "content_experiments", ["version_a_post_id"]
    )
    op.create_index(
        "ix_content_experiments_version_b_post_id", "content_experiments", ["version_b_post_id"]
    )


def downgrade() -> None:
    op.drop_table("content_experiments")
