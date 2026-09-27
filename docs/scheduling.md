# Scheduling

Schedules are persisted in PostgreSQL and exposed through `/api/v1/schedules`. Phase 12 adds automatic,
text-only execution through Celery Beat and the dedicated publishing worker.

## Workflow

1. A draft is approved with `POST /api/v1/posts/{id}/approve`.
2. An approved post is scheduled with `POST /api/v1/schedules`.
3. The supplied timezone-aware timestamp is stored in UTC. The IANA timezone is retained separately.
4. The post moves to `SCHEDULED` and the schedule becomes `ACTIVE`.
5. Cancelling the schedule returns an unpublished post to `APPROVED`.

Only one active or paused schedule is permitted per post. Every operation includes the authenticated
user identifier, so schedule and post identifiers owned by another user are not disclosed.

## Recurrence

Supported recurrence values are `ONCE`, `DAILY`, `WEEKDAYS`, `WEEKLY`, and `CUSTOM`. Weekly schedules
require weekday numbers from 0 (Monday) to 6 (Sunday). Custom schedules require timezone-aware dates.
These rules are stored as structured JSON. A schedule currently completes after publishing its bound post;
generating a sequence of distinct recurring posts remains a campaign-level enhancement.

## Lifecycle operations

- `PATCH /api/v1/schedules/{id}` changes the first publishing time and timezone.
- `POST /api/v1/schedules/{id}/pause` clears `next_run_at` without deleting the schedule.
- `POST /api/v1/schedules/{id}/resume` restores a future `next_run_at`.
- `POST /api/v1/schedules/{id}/cancel` permanently cancels the schedule.

Pausing an active campaign pauses its active schedules. Resuming the campaign resumes paused schedules;
cancelling a campaign cancels all active or paused schedules belonging to its posts.

## Automatic execution

No frontend timer performs publishing. Celery Beat scans once per minute and PostgreSQL remains the source
of truth. Claiming uses row locks with `SKIP LOCKED`, preventing two dispatchers from claiming the same post.
The worker records a publishing attempt before calling LinkedIn and finalizes the post and schedule afterward.

## Retry and recovery policy

- HTTP 429 responses are treated as definitive, safe failures and use persisted exponential backoff.
- Credential, permission, and validation failures are safe to retry only after the user corrects the cause.
- Network errors and server errors are treated as uncertain because LinkedIn may have accepted the post.
- Uncertain outcomes cannot be retried through the API or UI.
- Attempts are capped by `PUBLISHING_MAX_ATTEMPTS`.
- Each attempt has a distinct deterministic publishing-log key, preventing duplicate execution of the
  same attempt while still permitting a later safe attempt.

The calendar exposes **Retry safely** for failures whose publishing log explicitly records a safe outcome.
`POST /api/v1/schedules/{id}/retry` performs the same ownership, state, uncertainty, and attempt-limit checks.
