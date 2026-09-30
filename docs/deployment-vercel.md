# Deploying without a VPS

The production topology uses Vercel for the React frontend and a container host for FastAPI and
Celery. Vercel Functions cannot replace continuously running Celery workers or Celery Beat.

```text
Vercel (React/Vite)
        |
        v
Container host (FastAPI + worker/beat)
        |                 |
        v                 v
Supabase Postgres/S3   TLS Redis
```

## 1. Required managed services

- Supabase Postgres and S3-compatible storage (already supported by the application)
- A TLS Redis endpoint; Upstash Redis or a host-provided Redis-compatible service works
- A container host such as Render for the API and background processes
- Vercel for the frontend

For a low-cost initial deployment, run one API service and one Celery worker that also runs Beat.
For production reliability and queue isolation, use separate publishing, AI, background, and Beat
services as defined in `compose.yaml`.

## 2. Backend deployment

Deploy the repository with `backend/Dockerfile` and set the service root to `backend`.

API command:

```text
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Combined low-traffic worker command:

```text
uv run celery -A workers.celery_app:celery_app worker --beat --loglevel=INFO --queues=publishing,ai,default,research,analytics,notifications
```

For the production topology, create separate services using the commands from `compose.yaml`.

Set all backend variables from `.env.example`, especially:

- `APP_ENV=production`
- `DATABASE_URL` using the Supabase session pooler with `sslmode=require`
- `REDIS_URL` using a TLS `rediss://` URL when required by the provider
- a strong `JWT_SECRET`
- `CORS_ORIGINS=["https://YOUR-VERCEL-DOMAIN"]`
- LinkedIn client credentials and encryption key
- NVIDIA provider, model, and API key
- Supabase storage credentials

Run before serving production traffic:

```text
uv run alembic upgrade head
```

Verify `https://YOUR-BACKEND-HOST/api/v1/health` returns a healthy response.

## 3. Vercel frontend deployment

Import the Git repository into Vercel and configure:

- Root Directory: `frontend`
- Framework Preset: Vite
- Install Command: `pnpm install --frozen-lockfile`
- Build Command: `pnpm build`
- Output Directory: `dist`

Add this Vercel environment variable for Production and Preview as appropriate:

```text
VITE_API_BASE_URL=https://YOUR-BACKEND-HOST/api/v1
```

The included `frontend/vercel.json` provides the React Router SPA fallback. Redeploy after changing
environment variables because Vite embeds them at build time.

## 4. LinkedIn production callback

Set both the backend environment and LinkedIn Developer Portal authorized redirect URL to:

```text
https://YOUR-VERCEL-DOMAIN/settings/linkedin/callback
```

Set `LINKEDIN_REDIRECT_URI` to that exact URL. LinkedIn requires an exact match.

## 5. Final checks

1. Register and sign in from the Vercel domain.
2. Connect LinkedIn and complete the OAuth callback.
3. Generate and save a draft.
4. Schedule a post several minutes ahead.
5. Confirm the worker and Beat process remain running.
6. Confirm the scheduled post reaches a terminal publishing state.
7. Inspect API and worker logs without exposing tokens or secrets.

Do not deploy `.env`, service-role keys, LinkedIn secrets, NVIDIA keys, or storage secret keys to the
frontend project.

## 6. Oracle worker using Upstash Redis

`compose.oracle-worker.yaml` is the worker-only production Compose file. It has no local Redis
service: Celery connects exclusively to the `REDIS_URL` in the server's `.env` file. Use the exact
TLS `rediss://` endpoint supplied by Upstash.

On a 1 GB Oracle Always Free Micro instance, start only the scheduler and publishing worker:

```text
docker compose -f compose.oracle-worker.yaml up -d --build scheduler worker-publishing
```

The publishing worker also consumes the `default` queue so routine token cleanup tasks do not
accumulate. Start `worker-ai` and `worker-background` only on an instance with enough memory, such
as an Always Free Ampere A1 Flex instance.

Check their health with:

```text
docker compose -f compose.oracle-worker.yaml ps
docker compose -f compose.oracle-worker.yaml logs -f scheduler worker-publishing
```
# Vercel configuration

When the Vercel project root is this repository, Vercel uses the root `vercel.json`.
It builds `frontend/dist` and rewrites every client-side route to `index.html`, so a
browser refresh on routes such as `/create`, `/calendar`, or `/copilot` continues to
be handled by React Router instead of returning Vercel's 404 page.
