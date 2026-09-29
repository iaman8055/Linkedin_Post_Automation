# Copilot tool safety

J1 introduces a controlled tool allowlist between the AI model and application services. The model
never receives a database session, repository, access token, or arbitrary query capability.

## Rules

- Every tool call is validated with a strict Pydantic schema that rejects unknown fields.
- The authenticated user identifier is supplied by application code, never accepted from AI output.
- Repository-backed reads are constrained to the user's active workspace.
- Read tools may execute immediately.
- Write tools return `confirmation_required` unless application code explicitly executes the same
  validated call with `confirmed=True`.
- `create_draft` can only create a `DRAFT`; it cannot approve, schedule, or publish.
- No publishing tool is registered.
- Audit records contain tool name, workspace, risk outcome, and no generated or private content.

## Initial allowlist

Read tools: recent posts, top measured posts, writing profile, content ideas, content plans, explicitly
enabled knowledge, and calendar.

Write tools: create draft.

J2 will expose these capabilities through persisted Copilot conversations and one-time confirmation
actions. Adding a tool requires a schema, risk classification, workspace-aware handler, and tests.
