"""scope core content to workspaces

Revision ID: 9d8a2c4e6f10
Revises: f85ab4c6d43e
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9d8a2c4e6f10"
down_revision: str | None = "f85ab4c6d43e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONTENT_TABLES = (
    "posts",
    "campaigns",
    "content_ideas",
    "content_plans",
    "content_experiments",
    "knowledge_items",
    "templates",
    "writing_profiles",
)


def upgrade() -> None:
    for table_name in CONTENT_TABLES:
        with op.batch_alter_table(table_name) as batch:
            batch.add_column(sa.Column("workspace_id", sa.Uuid(), nullable=True))
            batch.create_index(f"ix_{table_name}_workspace_id", ["workspace_id"])
            batch.create_foreign_key(
                f"fk_{table_name}_workspace_id_workspaces",
                "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE",
            )

    bind = op.get_bind()
    metadata = sa.MetaData()
    workspaces = sa.Table("workspaces", metadata, autoload_with=bind)
    for table_name in CONTENT_TABLES:
        table = sa.Table(table_name, metadata, autoload_with=bind)
        default_workspace = (
            sa.select(workspaces.c.id)
            .where(
                workspaces.c.user_id == table.c.user_id,
                workspaces.c.is_default.is_(True),
            )
            .limit(1)
            .scalar_subquery()
        )
        bind.execute(
            table.update().where(table.c.workspace_id.is_(None))
            .values(workspace_id=default_workspace)
        )

    op.create_index(
        "ix_posts_workspace_status_created",
        "posts", ["workspace_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_posts_workspace_status_created", table_name="posts")
    for table_name in reversed(CONTENT_TABLES):
        with op.batch_alter_table(table_name) as batch:
            batch.drop_constraint(
                f"fk_{table_name}_workspace_id_workspaces", type_="foreignkey"
            )
            batch.drop_index(f"ix_{table_name}_workspace_id")
            batch.drop_column("workspace_id")
