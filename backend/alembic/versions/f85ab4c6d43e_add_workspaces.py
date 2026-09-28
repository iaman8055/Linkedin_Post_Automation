"""add workspace foundation

Revision ID: f85ab4c6d43e
Revises: e74fa3b5c32d
Create Date: 2026-09-28
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "f85ab4c6d43e"
down_revision: str | None = "e74fa3b5c32d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name"),
    )
    op.create_index("ix_workspaces_user_id", "workspaces", ["user_id"])
    with op.batch_alter_table("user_settings") as batch:
        batch.add_column(sa.Column("active_workspace_id", sa.Uuid(), nullable=True))
        batch.create_index("ix_user_settings_active_workspace_id", ["active_workspace_id"])
        batch.create_foreign_key(
            "fk_user_settings_active_workspace_id_workspaces",
            "workspaces", ["active_workspace_id"], ["id"], ondelete="SET NULL",
        )
    with op.batch_alter_table("linkedin_accounts") as batch:
        batch.add_column(sa.Column("workspace_id", sa.Uuid(), nullable=True))
        batch.create_index("ix_linkedin_accounts_workspace_id", ["workspace_id"])
        batch.create_foreign_key(
            "fk_linkedin_accounts_workspace_id_workspaces",
            "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE",
        )
        batch.drop_constraint("uq_linkedin_account_member", type_="unique")
        batch.create_unique_constraint(
            "uq_linkedin_account_workspace_member", ["workspace_id", "linkedin_member_id"]
        )

    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.Uuid()))
    workspaces = sa.table(
        "workspaces", sa.column("id", sa.Uuid()), sa.column("user_id", sa.Uuid()),
        sa.column("name", sa.String()), sa.column("kind", sa.String()),
        sa.column("is_default", sa.Boolean()), sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    settings = sa.table(
        "user_settings", sa.column("user_id", sa.Uuid()),
        sa.column("active_workspace_id", sa.Uuid()),
    )
    accounts = sa.table(
        "linkedin_accounts", sa.column("user_id", sa.Uuid()),
        sa.column("workspace_id", sa.Uuid()),
    )
    now = datetime.now(UTC)
    for user_id in bind.execute(sa.select(users.c.id)).scalars():
        workspace_id = uuid4()
        bind.execute(workspaces.insert().values(
            id=workspace_id, user_id=user_id, name="Personal", kind="personal",
            is_default=True, is_active=True, created_at=now, updated_at=now,
        ))
        bind.execute(
            settings.update().where(settings.c.user_id == user_id)
            .values(active_workspace_id=workspace_id)
        )
        bind.execute(
            accounts.update().where(accounts.c.user_id == user_id)
            .values(workspace_id=workspace_id)
        )


def downgrade() -> None:
    with op.batch_alter_table("linkedin_accounts") as batch:
        batch.drop_constraint("uq_linkedin_account_workspace_member", type_="unique")
        batch.create_unique_constraint(
            "uq_linkedin_account_member", ["user_id", "linkedin_member_id"]
        )
        batch.drop_constraint(
            "fk_linkedin_accounts_workspace_id_workspaces", type_="foreignkey"
        )
        batch.drop_index("ix_linkedin_accounts_workspace_id")
        batch.drop_column("workspace_id")
    with op.batch_alter_table("user_settings") as batch:
        batch.drop_constraint(
            "fk_user_settings_active_workspace_id_workspaces", type_="foreignkey"
        )
        batch.drop_index("ix_user_settings_active_workspace_id")
        batch.drop_column("active_workspace_id")
    op.drop_table("workspaces")
