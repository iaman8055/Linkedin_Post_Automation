import ssl

from celery import Celery  # type: ignore[import-untyped]
from kombu import Exchange, Queue  # type: ignore[import-untyped]

from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()
redis_url = settings.redis_url
if redis_url.startswith("rediss://") and "ssl_cert_reqs=" not in redis_url:
    separator = "&" if "?" in redis_url else "?"
    redis_url = f"{redis_url}{separator}ssl_cert_reqs=required"
tls_options = (
    {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    if settings.redis_url.startswith("rediss://")
    else None
)

celery_app = Celery(
    "linkedin_ai_autopilot",
    broker=redis_url,
    backend=redis_url,
    broker_use_ssl=tls_options,
    redis_backend_use_ssl=tls_options,
    include=[
        "workers.ai_tasks",
        "workers.publishing_tasks",
        "workers.system_tasks",
    ],
)

default_exchange = Exchange("linkedin_autopilot", type="direct")
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    enable_utc=True,
    timezone="UTC",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    task_soft_time_limit=settings.celery_task_soft_time_limit_seconds,
    task_time_limit=settings.celery_task_time_limit_seconds,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_always_eager,
    task_default_queue="default",
    task_default_exchange=default_exchange.name,
    task_default_routing_key="default",
    task_queues=(
        Queue("default", default_exchange, routing_key="default"),
        Queue("publishing", default_exchange, routing_key="publishing"),
        Queue("ai", default_exchange, routing_key="ai"),
        Queue("research", default_exchange, routing_key="research"),
        Queue("analytics", default_exchange, routing_key="analytics"),
        Queue("notifications", default_exchange, routing_key="notifications"),
    ),
    task_routes={
        "workers.ai_tasks.*": {"queue": "ai", "routing_key": "ai"},
        "workers.publishing_tasks.*": {
            "queue": "publishing",
            "routing_key": "publishing",
        },
        "workers.research_tasks.*": {"queue": "research", "routing_key": "research"},
        "workers.analytics_tasks.*": {"queue": "analytics", "routing_key": "analytics"},
        "workers.notification_tasks.*": {
            "queue": "notifications",
            "routing_key": "notifications",
        },
    },
    beat_schedule={
        "dispatch-due-linkedin-posts": {
            "task": "workers.publishing_tasks.dispatch_due_schedules",
            "schedule": 60.0,
            "options": {"queue": "publishing"},
        },
        "recover-stale-publishing-claims": {
            "task": "workers.publishing_tasks.recover_stale_publishing_claims",
            "schedule": 300.0,
            "options": {"queue": "publishing"},
        },
        "remove-expired-auth-tokens": {
            "task": "workers.system_tasks.remove_expired_auth_tokens",
            "schedule": 3600.0,
            "options": {"queue": "default"},
        }
    },
)
