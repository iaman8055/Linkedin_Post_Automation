# LinkedIn AI Autopilot

LinkedIn AI Autopilot is an AI-assisted workspace for planning, creating, reviewing, scheduling,
publishing, and analyzing LinkedIn content. Development follows an incremental milestone plan; the
current repository contains the Phase 1 application foundation.

## Current scope

- React and TypeScript frontend with routing, query management, Tailwind CSS, and a dashboard shell
- FastAPI backend with versioned routing, environment-based settings, structured logging, and health check
- Test, lint, and type-check tooling for both applications
- Docker Compose topology for the frontend, backend, PostgreSQL, and Redis

No LinkedIn, AI, research, analytics, or publishing API is simulated. Those integrations are added in
their scheduled phases after their current provider requirements are verified.

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
Phase 1 needs no real external-service credentials.

## Frontend development

```powershell
pnpm install
pnpm dev
```

The frontend is available at `http://localhost:5173`.

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

Worker and scheduler services are added with the real Celery application in Phase 11. Phase 1 does not
include placeholder workers.

## Database migrations

SQLAlchemy models and the Alembic migration environment are created in Phase 2. Schema changes must be
made through Alembic migrations after that phase.

## LinkedIn developer setup

LinkedIn OAuth and publishing are implemented in Phases 4 and 5. Before implementation, the current
LinkedIn products, scopes, endpoints, application approval, and rate limits will be verified. Add no
LinkedIn credentials until those phases.

## AI provider setup

The provider-neutral AI abstraction is introduced in Phase 6. A provider and API key are not required
for Phase 1.

## Deployment notes

The current containers support local development. Production deployment hardening, secret injection,
TLS termination, managed PostgreSQL/Redis, object storage, monitoring, and backup guidance belong to
Phase 24.

## Known limitations

- The dashboard is an application shell; feature screens arrive in later phases.
- Database entities and migrations begin in Phase 2.
- Authentication begins in Phase 3.
- Docker must be installed separately before Compose can be run locally.
- External APIs are deliberately not called or mocked in production code.
