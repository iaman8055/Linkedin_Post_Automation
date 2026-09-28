# Content ideas, repurposing, and planning

Milestone C adds one connected content workflow at `/studio` without creating a second post or
scheduling system. Every generated post is stored in the existing `posts` table and remains owned by
the authenticated user.

## Ideas

`POST /api/v1/ideas/generate` returns structured, unsaved suggestions. Saving is an explicit action via
`POST /api/v1/ideas`; a saved idea can be converted to a reviewable draft with
`POST /api/v1/ideas/{id}/create-post`. The source idea is then marked `USED`.

## Repurposing

`POST /api/v1/ai/repurpose` accepts source content, an output format, and a variation count. The AI is
instructed to preserve the source meaning, avoid unsupported claims, and produce distinct angles rather
than duplicate posts. Results are saved as `DRAFT` posts. URL text must already have been extracted by
the research workflow; this endpoint does not perform unrestricted URL fetching.

## Content plans

`POST /api/v1/content-plans/generate` creates a persisted plan with timezone-aware posting slots and
complete draft content. Supported cadences are two, three, or five weekdays per week, plus daily.

Approval is intentionally safe:

- The default approval action creates dated draft posts only.
- `schedule_for_auto_publish=true` is an explicit opt-in that creates active, one-time records in the
  existing `schedules` table and moves the posts to `SCHEDULED`.
- Passed dates are rejected before any automatic schedule is created.
- The existing Celery publishing worker remains the only automatic publishing path.

Apply the schema changes before using the feature:

```powershell
cd backend
uv run alembic upgrade head
```
