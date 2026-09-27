# Templates

Templates are user-owned reusable structures for LinkedIn post drafts. They provide deterministic text
substitution and do not call an AI provider. The frontend is available at `/templates`; the API is under
`/api/v1/templates`.

## Placeholder syntax

Placeholders use a named, double-brace form such as `{{topic}}`, `{{audience}}`, or `{{key_insight}}`.
Names must begin with a letter and may contain letters, digits, and underscores. Whitespace inside the
braces is accepted and normalized during detection. Malformed braces are rejected rather than silently
stored.

Rendering requires exactly the values used by the template: missing and unknown values both produce a
validation error. The rendered result may not exceed the post content limit of 3,000 characters.

## Lifecycle and ownership

Templates are active when created. An active template can be edited, rendered, archived, or deleted.
Archived templates remain visible when requested and can be restored, but cannot be rendered. Every
query is scoped to the authenticated user, so a template owned by another user behaves as not found.

Deleting a template is permanent. Archiving is the preferred reversible action for templates that may
be useful later.

## API

- `POST /api/v1/templates` creates a template.
- `GET /api/v1/templates` lists templates with search, status, limit, and offset filters.
- `GET /api/v1/templates/{template_id}` returns one owned template.
- `PATCH /api/v1/templates/{template_id}` updates an active template.
- `DELETE /api/v1/templates/{template_id}` permanently deletes a template.
- `POST /api/v1/templates/{template_id}/archive` archives a template.
- `POST /api/v1/templates/{template_id}/restore` restores a template.
- `POST /api/v1/templates/{template_id}/render` validates values and returns rendered content.

The browser's **Use template** flow renders through the backend, then creates a normal post through the
existing post API and opens it in the editor. This preserves the post service's ownership and lifecycle
rules instead of bypassing them.
