# Architecture

LinkedIn AI Autopilot starts as a modular monolith with background workers.

## Request path

1. The React application calls versioned REST endpoints.
2. FastAPI routers handle HTTP concerns and delegate to services.
3. Services own business rules and use repositories for persistence.
4. Repositories access PostgreSQL through SQLAlchemy.
5. Long-running work is delegated to dedicated Celery queues through Redis.

## Module boundaries

External providers are isolated behind client and service abstractions. LinkedIn, AI, research,
storage, and analytics details must not leak into routers or persistence models.

PostgreSQL is the source of truth for scheduling and publishing state. Background task delivery is
treated as at-least-once, so publishing operations must become idempotent before automatic publishing
is enabled.

