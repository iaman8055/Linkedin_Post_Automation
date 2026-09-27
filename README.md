# LinkedIn AI Autopilot

LinkedIn AI Autopilot is an AI-assisted workspace for planning, creating, reviewing, scheduling,
publishing, and analyzing LinkedIn content. Development follows an incremental milestone plan; the
current repository contains the Phase 13 foundation, including AI draft generation, campaigns,
scheduling, automatic text-only LinkedIn publishing, and safe retry/recovery controls.

## Current scope

- Production-oriented React and TypeScript frontend with protected routing, persisted authentication,
  responsive navigation, query management, forms, validation, and a compact Tailwind design system
- FastAPI backend with versioned routing, environment-based settings, structured logging, and health check
- SQLAlchemy 2 domain models, user-scoped repositories, and Alembic migrations
- Argon2 password hashing, JWT access tokens, rotating refresh tokens, and authorization dependencies
- LinkedIn OpenID Connect OAuth with signed state and encrypted token storage
- Permission-gated LinkedIn test posts with publishing logs and request idempotency
- Provider-neutral AI contracts, provider registration, safe execution tracking, and configuration status
- User-owned post CRUD with search, pagination, draft mutation rules, editor, and approximate preview
- OpenAI Responses API adapter with structured multi-post generation saved as reviewable drafts
- Campaign CRUD, legal lifecycle transitions, approval modes, timezone settings, and post organization
- Post approval plus UTC-backed one-time, daily, weekday, weekly, and custom-date schedules
- Schedule listing, rescheduling, cancellation, pause/resume, and campaign-level schedule pausing
- Celery workers with isolated publishing, AI, research, analytics, and notification queues
- Celery Beat with a real hourly expired-auth-token cleanup task
- Minute-based due-schedule dispatch with PostgreSQL row locking and automatic LinkedIn publication
- Exponential rate-limit retries, explicit safe retries, attempt limits, and stale-worker recovery
- Test, lint, and type-check tooling for both applications
- Docker Compose topology for the frontend, backend, PostgreSQL, and Redis

No external API is simulated in production code. Concrete AI, research, analytics, and automated
publishing integrations are added in their scheduled phases after provider requirements are verified.

## Architecture

The system uses a modular monolith with background workers:

```text
React frontend -> FastAPI REST API -> PostgreSQL
                         |
                         +-> Redis -> Celery workers
                         |
                         +-> LinkedIn / AI / research providers
```

Backend modules follow router -> service -> repository -> database boundaries. Frontend code is grouped
by feature. See [docs/architecture.md](docs/architecture.md) for the architectural constraints.

## Prerequisites

- Node.js 22 or newer and pnpm 11
- Python 3.12 and uv
- Docker Desktop with Docker Compose for the container workflow

## Configuration

Copy `.env.example` to `.env` and replace development placeholders where required. Never commit `.env`.
Phase 3 requires a strong `JWT_SECRET`; transactional email remains deliberately unconfigured.

## Frontend development

```powershell
pnpm install
pnpm dev
```

The frontend is available at `http://localhost:5173`.

Implemented screens cover the complete Phase 1-13 backend surface: sign in and registration, dashboard,
post library and editor, AI-assisted draft generation, campaigns and campaign detail, LinkedIn connection
and OAuth callback handling, LinkedIn test publishing, and settings. Routes belonging to later phases are
visible as explicit unavailable states and never display fabricated production data.

## Backend development

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`; development API documentation is at `/docs` and the
health endpoint is at `/api/v1/health`.

## Quality checks

```powershell
pnpm lint
pnpm typecheck
pnpm test
pnpm build

cd backend
uv run ruff check .
uv run mypy app workers
uv run pytest --cov=app
```

## Docker

After creating `.env` from `.env.example`:

```powershell
docker compose up --build
```

Compose starts dedicated publishing and AI workers, a shared background worker for lower-volume queues,
and Celery Beat. See [docs/background-workers.md](docs/background-workers.md) for responsibilities and
individual development commands.

## Database migrations

From the `backend` directory, apply the current schema with:

```powershell
uv run alembic upgrade head
```

Create future migrations with `uv run alembic revision --autogenerate -m "description"`. Review every
generated revision and verify its upgrade and downgrade paths. See
[docs/database.md](docs/database.md) for the schema conventions.

## LinkedIn developer setup

LinkedIn OAuth requests `openid profile email w_member_social`. Text-only test publishing uses the
versioned Posts API and requires the Share on LinkedIn product. See
[docs/linkedin-oauth.md](docs/linkedin-oauth.md) for Developer Portal setup and current restrictions.

## AI provider setup

The provider-neutral layer includes a verified OpenAI Responses API adapter, strict structured output,
safe `AIJob` tracking, and multi-post draft generation. AI remains disabled until `AI_PROVIDER=openai`,
`AI_MODEL`, and `AI_API_KEY` are configured. See
[docs/ai-provider.md](docs/ai-provider.md) for the integration contract and data-handling rules.

## Authentication

Authentication routes are available under `/api/v1/auth`. Copy `.env.example` to `.env` and replace
`JWT_SECRET` with a long, unpredictable value before use. See
[docs/authentication.md](docs/authentication.md) for endpoint and token behavior.

## Post editor

Authenticated users can create and edit manual drafts at `/create` and browse saved posts at `/posts`.
The API is available under `/api/v1/posts`. See [docs/posts.md](docs/posts.md) for ownership, validation,
pagination, and lifecycle rules.

## Campaigns

Authenticated users can create and manage campaigns at `/campaigns`, organize existing posts, choose
manual or automatic approval, and apply legal lifecycle transitions. New campaigns default to manual
approval. See [docs/campaigns.md](docs/campaigns.md).

## Scheduling

Approved posts can be planned at `/calendar`. Schedule timestamps are normalized to UTC while the
requested IANA timezone is retained for display and future recurrence calculation. The API is under
`/api/v1/schedules`; see [docs/scheduling.md](docs/scheduling.md) for lifecycle and worker boundaries.

## Deployment notes

The current containers support local development. Production deployment hardening, secret injection,
TLS termination, managed PostgreSQL/Redis, object storage, monitoring, and backup guidance belong to
Phase 24.

## Known limitations

- Templates, research, analytics, insights, and notifications remain unavailable
  until their backend phases are implemented. Their frontend routes state that limitation explicitly.
- Transactional email delivery and Redis-backed authentication rate limiting are not configured yet.
- LinkedIn connection requires real Developer Portal credentials and an approved OpenID Connect product.
- LinkedIn publishing is text-only. Media support arrives in Phase 19.
- Network or server outcomes that may have reached LinkedIn are deliberately marked uncertain and cannot
  be retried automatically, because the available member permissions do not guarantee reconciliation.
- AI generation requires a real OpenAI API key and access to the configured model; automated tests use only local provider boundaries.
- Docker must be installed separately before Compose can be run locally.
- External APIs are deliberately not called or mocked in production code.
