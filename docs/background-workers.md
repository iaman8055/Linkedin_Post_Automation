# Background workers

Phase 11 adds a real Celery application backed by Redis. PostgreSQL remains the source of truth for posts,
schedules, jobs, and authentication records; Redis carries transient task messages and short-lived results.

## Queue topology

| Queue | Responsibility |
| --- | --- |
| `publishing` | Due-schedule claiming and automatic text-only LinkedIn publishing |
| `ai` | Real AI draft generation through the configured provider |
| `research` | Live provider research and attributable source persistence |
| `analytics` | Permission-gated LinkedIn post metric collection |
| `notifications` | Reserved for Phase 22 notification delivery |
| `default` | Internal maintenance tasks |

Tasks use JSON serialization, late acknowledgements, worker-loss rejection, UTC, bounded execution times,
and a prefetch multiplier of one. External-provider retry policy remains task-specific so application or
validation errors are not retried indiscriminately.

## Celery Beat

Beat currently runs `remove_expired_auth_tokens` once per hour. This is a real database maintenance task.
Beat dispatches `dispatch_due_schedules` once per minute. PostgreSQL row locks with `SKIP LOCKED` claim
due schedules, change their posts to `PUBLISHING`, and enqueue one publishing task per claimed schedule.
Every five minutes, `recover_stale_publishing_claims` examines claims older than the configured threshold.
Claims with no started external attempt are safely requeued; claims that may have reached LinkedIn are
marked as uncertain failures and are not retried.

## Local Docker workflow

`docker compose up --build` starts:

- `worker-publishing`, consuming only `publishing`
- `worker-ai`, consuming only `ai`
- `worker-background`, consuming `default`, `research`, `analytics`, and `notifications`
- `scheduler`, running Celery Beat

To run a process directly from `backend` during development:

```powershell
uv run celery -A workers.celery_app:celery_app worker --loglevel=INFO --queues=ai
uv run celery -A workers.celery_app:celery_app beat --loglevel=INFO
```

## Configuration

- `REDIS_URL` configures both the broker and short-lived result backend.
- `CELERY_WORKER_PREFETCH_MULTIPLIER` defaults to `1`.
- `CELERY_TASK_SOFT_TIME_LIMIT_SECONDS` defaults to `270`.
- `CELERY_TASK_TIME_LIMIT_SECONDS` defaults to `300`.
- `CELERY_TASK_ALWAYS_EAGER` is intended only for controlled tests and must remain `false` in deployed environments.
- `PUBLISHING_MAX_ATTEMPTS` defaults to `5`.
- `PUBLISHING_RETRY_BASE_SECONDS` and `PUBLISHING_RETRY_MAX_SECONDS` bound exponential backoff.
- `PUBLISHING_STALE_CLAIM_MINUTES` defaults to `15`.

The analytics and notification modules document their phase boundaries but register no fake provider
tasks. Research calls the configured real provider, and automatic publishing calls LinkedIn's real Posts API only when a due schedule and a valid,
permissioned LinkedIn account are present.
