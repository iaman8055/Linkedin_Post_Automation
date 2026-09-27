# Post creation and editing

Phase 7 introduces authenticated, user-owned post drafts and a manual editor. AI generation,
approval, scheduling, media, and automated publishing remain separate later milestones.

## API

All routes require a valid bearer access token and are scoped to the authenticated user:

- `POST /api/v1/posts` creates a draft.
- `GET /api/v1/posts` lists posts with `status`, `search`, `offset`, and `limit` filters.
- `GET /api/v1/posts/{id}` returns one owned post.
- `PATCH /api/v1/posts/{id}` edits a draft.
- `DELETE /api/v1/posts/{id}` deletes a draft.

Requests for another user's identifier return the same `POST_NOT_FOUND` response as a missing record.
List results are newest-first and paginated, with a maximum page size of 100.

## Draft rules

New records always start in `DRAFT`; clients cannot set the lifecycle state. Content is trimmed,
validated to 3,000 characters, and fingerprinted whenever it changes. Only drafts can be edited or
deleted. This prevents the editor from mutating approved, scheduled, publishing, or published content
outside the lifecycle services introduced in later phases.

The title is an internal organizational label and is not part of the LinkedIn post body. A blank title
is stored as `null`.

## Frontend

`/create` opens a new draft editor, `/create/{id}` edits an existing draft, and `/posts` displays the
current user's searchable content library. The preview is intentionally labelled as approximate and
does not claim to reproduce LinkedIn's interface exactly.

The API client reads the Phase 3 access token from the browser's `access_token` local-storage entry.
A complete sign-in screen and browser token lifecycle are still future frontend work.
