import logging
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.schemas.research import ResearchSearchRequest
from app.services.research.registry import create_research_provider
from app.services.research.service import ResearchService
from workers.celery_app import celery_app
from workers.database import worker_session

logger = logging.getLogger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.research_tasks.research_topic",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def research_topic(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    with worker_session() as session:
        answer, provider, sources = ResearchService(
            session, create_research_provider(settings)
        ).search(UUID(user_id), ResearchSearchRequest.model_validate(payload))
        logger.info(
            "background_research_completed",
            extra={"user_id": user_id, "provider": provider, "source_count": len(sources)},
        )
        return {
            "answer": answer,
            "provider": provider,
            "source_ids": [str(source.id) for source in sources],
        }
