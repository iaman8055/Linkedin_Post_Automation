# Engagement Lab

Milestone F adds review-only comment assistance and measurable A/B content experiments at
`/engagement`.

## Comment Assistant

`POST /api/v1/comments/generate-response` accepts a pasted comment and optional post context. It
returns one editable suggestion for each supported style: professional, friendly, concise, thoughtful,
and humorous.

Suggestions are not posted to LinkedIn. The user must review, edit, and copy the text. This application
does not claim access to LinkedIn comment APIs or use browser automation as a substitute.

## Content experiments

`POST /api/v1/experiments` creates two distinct draft posts from an owned source post. The requested
comparison axis is limited to hook, CTA, structure, tone, or length. Both variants use the normal post
editor, approval, scheduling, and publishing workflow.

`GET /api/v1/experiments/{id}/comparison` follows these rules:

- before both posts are published, the status is `awaiting_publication`;
- without a real analytics snapshot for both versions, the status is `awaiting_analytics`;
- a leading version is named only when both latest snapshots contain engagement rates and one is
  strictly higher;
- equal or unavailable rates produce no winner.

The comparison is descriptive and does not claim that a variant is universally better.

Apply the migration before using experiments:

```powershell
cd backend
uv run alembic upgrade head
```
