# LinkedIn AI Autopilot

LinkedIn AI Autopilot is an AI-assisted workspace for planning, creating, reviewing, scheduling,
publishing, and analyzing LinkedIn content. Development follows an incremental milestone plan; the
current repository contains the Phase 20 foundation, including AI draft generation, campaigns,
publishing, research, quality checks, media, and permission-gated LinkedIn analytics.

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
- Month calendar, status-coded post placement, selected-day agenda, and schedule management controls
- User-owned reusable templates with validated placeholders, archive/restore, preview rendering, and
  draft creation from rendered content
- Personal writing profiles with default-profile management and optional AI-generation guidance for
  tone, sentence style, language, emoji use, paragraph length, technical depth, CTAs, and vocabulary
- Provider-neutral research with a real Tavily adapter, freshness filters, attributable source storage,
  a saved-source library, provider summaries, and source-grounded AI draft creation
- Non-destructive quality checks for repetition, hashtags, emoji use, formatting, length, duplicates,
  grammar, unsupported claims, and potentially misleading claims
- User-uploaded image, MP4, and PDF attachments with signature validation, bounded file sizes,
  authenticated retrieval, metadata-only database records, and pluggable binary storage
- LinkedIn member-post analytics snapshots for impressions, reactions, comments, reshares, and derived
  engagement rate, available only with the restricted Community Management permission
- Test, lint, and type-check tooling for both applications
- Docker Compose topology for the frontend, backend, PostgreSQL, and Redis

No external API is simulated in production code. Concrete AI, research, and automated
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

Implemented screens cover the complete Phase 1-20 backend surface: sign in and registration, dashboard,
post library and editor, AI-assisted draft generation, campaigns and campaign detail, LinkedIn connection
and OAuth callback handling, LinkedIn test publishing, templates, writing profiles, research, quality checks, media attachments, analytics, and settings. Routes belonging to later
phases are visible as explicit unavailable states and never display fabricated production data.

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

The provider-neutral layer includes OpenAI and NVIDIA Nemotron adapters, structured output,
safe `AIJob` tracking, and multi-post draft generation. For Nemotron, configure `AI_PROVIDER=nvidia`,
`AI_MODEL`, and `NVIDIA_API_KEY`. See
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

## Templates

Authenticated users can create reusable post structures at `/templates`, insert named placeholders such
as `{{topic}}`, preview rendered content, and create a real draft from the result. Templates can be
archived without losing their history. See [docs/templates.md](docs/templates.md) for syntax, lifecycle,
validation, and API behavior.

## Writing profiles

Users can manage personal style profiles from `/settings/writing-profiles` and optionally select one
when generating AI drafts. The backend resolves profiles by the authenticated owner and injects only
bounded style data into the generation requirements. See
[docs/writing-profiles.md](docs/writing-profiles.md) for lifecycle and API details.

## Research provider setup

The research workspace at `/research` uses Tavily only when `RESEARCH_PROVIDER=tavily` and
`RESEARCH_API_KEY` are configured. Searches persist the real returned URLs and snippets; selected
sources can ground a generated draft and remain linked to it. See [docs/research.md](docs/research.md).

## Content studio

The `/studio` workspace combines AI content ideas, source-to-content repurposing, and content planning.
Generated work enters the existing post lifecycle as a draft. Plan approval schedules automatic
publishing only when the user explicitly opts in. See
[docs/content-workflows.md](docs/content-workflows.md) for API and safety behavior.

## Writing style and personal knowledge

Writing profiles can now be suggested from the user's own post samples and remain manually editable.
The private knowledge workspace stores reusable personal context, but only explicitly selected items are
included in a generation request. See
[docs/writing-style-and-knowledge.md](docs/writing-style-and-knowledge.md).

## Engagement Lab

The `/engagement` workspace provides editable AI comment-response suggestions and controlled A/B post
experiments. Replies are never posted automatically, and experiment comparisons require real analytics
for both published versions. See [docs/engagement-lab.md](docs/engagement-lab.md).

## Creator progress

The dashboard includes professional publishing goals, activity-based levels, streaks, and earned
milestones. Impression achievements require real collected LinkedIn analytics. See
[docs/creator-progress.md](docs/creator-progress.md).

## Workspaces

Settings supports owned personal, company, and client workspaces. LinkedIn OAuth connections are scoped
to the current workspace, with existing accounts migrated into a default Personal workspace. Content
records remain user-owned until the subsequent isolation migration. See [docs/workspaces.md](docs/workspaces.md).

## Quality checker

Saved posts expose an advisory quality check from the editor. Structural checks always run locally;
grammar and claim review are added when the configured AI provider is available. Results never alter
post content automatically. See [docs/quality-checker.md](docs/quality-checker.md).

## Media

Draft posts accept validated image, MP4 video, and PDF attachments. Development stores binary files in
an ignored local directory or Docker volume while PostgreSQL contains metadata only. Production rejects
local storage and includes an S3-compatible adapter for managed object storage. See
[docs/media.md](docs/media.md).

## Analytics

The analytics workspace stores only metrics returned by LinkedIn for the user's own published posts.
Collection requires Community Management API approval and `r_member_postAnalytics`; unavailable values
remain absent. See [docs/analytics.md](docs/analytics.md).

## Deployment notes

The current containers support local development. Production deployment hardening, secret injection,
TLS termination, managed PostgreSQL/Redis, object storage, monitoring, and backup guidance belong to
Phase 24.

## Known limitations

- Performance insights and notifications remain unavailable
  until their backend phases are implemented. Their frontend routes state that limitation explicitly.
- Transactional email delivery and Redis-backed authentication rate limiting are not configured yet.
- LinkedIn connection requires real Developer Portal credentials and an approved OpenID Connect product.
- LinkedIn publishing remains text-only. Phase 19 stores and manages attachments but does not claim
  access to LinkedIn's separate media-upload APIs or permissions.
- Network or server outcomes that may have reached LinkedIn are deliberately marked uncertain and cannot
  be retried automatically, because the available member permissions do not guarantee reconciliation.
- AI generation requires a real OpenAI API key and access to the configured model; automated tests use only local provider boundaries.
- Docker must be installed separately before Compose can be run locally.
- External APIs are deliberately not called or mocked in production code.
