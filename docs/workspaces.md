# Workspace and multi-account foundation

Milestone H introduces owned workspaces and workspace-scoped LinkedIn OAuth connections without
bypassing LinkedIn account or product restrictions.

## Behavior

- Every new user receives a default `Personal` workspace during registration.
- The migration creates the same default workspace for every existing user and assigns existing
  LinkedIn connections to it.
- Users can create personal, company, or client workspaces and select one as current.
- A workspace cannot be archived while it is the default or current workspace.
- LinkedIn connection status and new OAuth connections are scoped to the current workspace.
- The workspace ID is signed into the OAuth state. The callback therefore remains attached to the
  workspace that initiated consent, even if the current workspace changes in another browser tab.
- Each LinkedIn identity still requires legitimate OAuth consent and the appropriate LinkedIn products
  and scopes.

## Current boundary

This milestone is the multi-account foundation requested for an application that originally supported
one LinkedIn identity. LinkedIn connections are workspace-scoped now. Existing posts, campaigns,
templates, knowledge, analytics, and schedules remain user-owned until their records receive workspace
foreign keys in a later migration. The interface does not claim those resources are isolated yet.

## API

- `GET /api/v1/workspaces`
- `POST /api/v1/workspaces`
- `POST /api/v1/workspaces/{id}/activate`
- `PATCH /api/v1/workspaces/{id}`

Apply the migration before opening Settings:

```powershell
cd backend
uv run alembic upgrade head
```
