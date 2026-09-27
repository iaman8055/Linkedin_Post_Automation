import logging
from uuid import UUID

from app.core.config import get_settings
from app.services.analytics import AnalyticsService
from app.services.linkedin.client import LinkedInClient
from workers.celery_app import celery_app
from workers.database import worker_session

logger = logging.getLogger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.analytics_tasks.fetch_analytics",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=900,
    retry_jitter=True,
    max_retries=3,
)
def fetch_analytics(user_id: str, post_id: str) -> dict[str, str | int | float | None]:
    settings = get_settings()
    with worker_session() as session:
        snapshot = AnalyticsService(session, settings, LinkedInClient()).collect(
            UUID(user_id), UUID(post_id)
        )
        logger.info(
            "linkedin_analytics_collected",
            extra={"user_id": user_id, "post_id": post_id, "snapshot_id": str(snapshot.id)},
        )
        return {
            "snapshot_id": str(snapshot.id),
            "impressions": snapshot.impressions,
            "likes": snapshot.likes,
            "comments": snapshot.comments,
            "shares": snapshot.shares,
            "engagement_rate": snapshot.engagement_rate,
        }
