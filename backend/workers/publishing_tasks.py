from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.models.enums import ScheduleStatus
from app.models.schedule import Schedule
from app.repositories.schedule import ScheduleRepository
from app.services.linkedin.client import LinkedInClient
from app.services.publishing.recovery import PublishingRecoveryService
from app.services.publishing.scheduled_post import ScheduledPostPublisher
from workers.celery_app import celery_app
from workers.database import worker_session


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.publishing_tasks.list_due_schedule_ids"
)
def list_due_schedule_ids(limit: int = 100) -> list[str]:
    """Read due schedule identifiers without claiming or publishing them.

    Phase 12 will replace this diagnostic boundary with transactional claiming and
    idempotent LinkedIn publication.
    """
    safe_limit = min(max(limit, 1), 1000)
    with worker_session() as session:
        statement = (
            select(Schedule.id)
            .where(
                Schedule.status == ScheduleStatus.ACTIVE,
                Schedule.next_run_at.is_not(None),
                Schedule.next_run_at <= datetime.now(UTC),
            )
            .order_by(Schedule.next_run_at)
            .limit(safe_limit)
        )
        return [str(schedule_id) for schedule_id in session.scalars(statement)]


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.publishing_tasks.dispatch_due_schedules"
)
def dispatch_due_schedules(limit: int = 100) -> list[str]:
    safe_limit = min(max(limit, 1), 1000)
    with worker_session() as session:
        schedules = ScheduleRepository(session).claim_due(datetime.now(UTC), limit=safe_limit)
        schedule_ids = [str(schedule.id) for schedule in schedules]
    for schedule_id in schedule_ids:
        publish_scheduled_post.apply_async(args=[schedule_id], queue="publishing")
    return schedule_ids


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.publishing_tasks.publish_scheduled_post"
)
def publish_scheduled_post(schedule_id: str) -> dict[str, str]:
    settings = get_settings()
    with worker_session() as session:
        schedule = ScheduledPostPublisher(
            session,
            settings,
            LinkedInClient(timeout_seconds=30.0),
        ).publish(UUID(schedule_id))
        return {
            "schedule_id": str(schedule.id),
            "post_id": str(schedule.post_id),
            "status": schedule.status.value,
        }


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.publishing_tasks.recover_stale_publishing_claims"
)
def recover_stale_publishing_claims(limit: int = 100) -> dict[str, int]:
    settings = get_settings()
    with worker_session() as session:
        return PublishingRecoveryService(session, settings).recover_stale_claims(
            limit=min(max(limit, 1), 1000)
        )
