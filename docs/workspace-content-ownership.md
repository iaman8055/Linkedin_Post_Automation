# Workspace content ownership

J0 extends workspaces from LinkedIn identity selection into the ownership boundary for core content.

The following records now carry `workspace_id`: posts, campaigns, content ideas, content plans,
content experiments, knowledge items, templates, and writing profiles. Existing records are assigned
to their owner's default workspace by Alembic migration `9d8a2c4e6f10`.

## Compatibility stage

The new columns are nullable for one migration stage so deployments can roll forward without breaking
older application instances during a rolling release. Application-created records always receive the
authenticated user's active workspace. Repository reads require both the user and active workspace.
Legacy null-workspace records remain visible to their owning user only until the backfill has completed.

A later hardening migration may set these columns to `NOT NULL` after production backfill verification.

## Operational steps

```powershell
cd backend
uv run alembic upgrade head
```

After migration, switching the active workspace changes the visible core content as well as the active
LinkedIn identity. API paths and response bodies remain backward compatible.
