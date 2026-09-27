import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.ai_job import AIJob
from app.models.enums import AIJobStatus
from app.repositories.ai_job import AIJobRepository
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult, AIProviderError
from app.services.ai.registry import AIProviderRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AIExecution:
    job: AIJob
    result: AIGenerationResult


class AIExecutionService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        registry: AIProviderRegistry,
    ) -> None:
        self.session = session
        self.settings = settings
        self.registry = registry
        self.jobs = AIJobRepository(session)

    def execute(self, *, user_id: UUID, job_type: str, request: AIGenerationRequest) -> AIExecution:
        provider_name = self.settings.ai_provider
        if not provider_name:
            raise ApplicationError(
                "AI_PROVIDER_NOT_CONFIGURED", "AI provider is not configured.", 503
            )
        provider = self.registry.get(provider_name)
        if provider is None:
            raise ApplicationError(
                "AI_PROVIDER_UNAVAILABLE",
                "The configured AI provider is not installed.",
                503,
            )

        job = self.jobs.create_for_user(
            user_id,
            job_type=job_type,
            status=AIJobStatus.RUNNING,
            provider=provider.name,
            input_data={
                "model": request.model,
                "message_count": len(request.messages),
                "max_output_tokens": request.max_output_tokens,
                "temperature": request.temperature,
                "structured_output_requested": request.response_schema is not None,
            },
        )
        self.session.commit()

        try:
            result = provider.generate(request)
        except AIProviderError as exc:
            job.status = AIJobStatus.FAILED
            job.error_code = exc.code
            job.error_message = "AI generation failed."
            job.output_data = {"retryable": exc.retryable}
            self.session.commit()
            logger.warning(
                "ai_generation_failed",
                extra={"user_id": str(user_id), "job_id": str(job.id), "code": exc.code},
            )
            raise ApplicationError("AI_GENERATION_FAILED", "AI generation failed.", 502) from exc

        job.status = AIJobStatus.SUCCEEDED
        job.provider_job_id = result.provider_request_id
        job.output_data = {
            "model": result.model,
            "finish_reason": result.finish_reason,
            "usage": result.usage.model_dump(),
            "has_structured_output": result.structured_output is not None,
        }
        self.session.commit()
        logger.info(
            "ai_generation_succeeded",
            extra={"user_id": str(user_id), "job_id": str(job.id)},
        )
        return AIExecution(job=job, result=result)
