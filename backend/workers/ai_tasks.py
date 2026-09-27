import logging
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.schemas.ai import GeneratePostsRequest
from app.services.ai.content_generator import ContentGenerator
from app.services.ai.registry import create_provider_registry
from workers.celery_app import celery_app
from workers.database import worker_session

logger = logging.getLogger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.ai_tasks.generate_post",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def generate_post(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Generate real draft records through the configured AI provider."""
    parsed_user_id = UUID(user_id)
    request = GeneratePostsRequest.model_validate(payload)
    settings = get_settings()
    with worker_session() as session:
        job_id, posts = ContentGenerator(
            session, settings, create_provider_registry(settings)
        ).generate_posts(parsed_user_id, request)
        logger.info(
            "background_ai_generation_completed",
            extra={"user_id": user_id, "job_id": str(job_id), "post_count": len(posts)},
        )
        return {"job_id": str(job_id), "post_ids": [str(post.id) for post in posts]}
