from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import AIJobStatus
from app.models.user import User
from app.services.ai.contracts import (
    AIGenerationRequest,
    AIGenerationResult,
    AIMessage,
    AIMessageRole,
    AIProviderError,
    AIUsage,
)
from app.services.ai.execution import AIExecutionService
from app.services.ai.registry import AIProviderRegistry


class SuccessfulProvider:
    name = "test-provider"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        assert request.messages[0].content == "Sensitive prompt content"
        return AIGenerationResult(
            text="Generated response",
            provider=self.name,
            model=request.model,
            provider_request_id="provider-request-123",
            finish_reason="stop",
            usage=AIUsage(input_tokens=4, output_tokens=2, total_tokens=6),
        )


class FailingProvider:
    name = "failing-provider"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        raise AIProviderError("PROVIDER_TIMEOUT", "provider details", retryable=True)


def generation_request() -> AIGenerationRequest:
    return AIGenerationRequest(
        messages=[AIMessage(role=AIMessageRole.USER, content="Sensitive prompt content")],
        model="provider-model",
        max_output_tokens=500,
    )


def create_user(db_session: Session, email: str) -> UUID:
    user = User(email=email, password_hash="hashed", display_name="AI User")
    db_session.add(user)
    db_session.commit()
    return user.id


def test_ai_execution_tracks_safe_metadata_without_prompt_content(db_session: Session) -> None:
    registry = AIProviderRegistry()
    registry.register(SuccessfulProvider())
    settings = Settings(ai_provider="test-provider", ai_model="provider-model")
    service = AIExecutionService(db_session, settings, registry)
    user_id = create_user(db_session, "success@example.com")

    execution = service.execute(
        user_id=user_id,
        job_type="contract_test",
        request=generation_request(),
    )

    assert execution.result.text == "Generated response"
    assert execution.job.status is AIJobStatus.SUCCEEDED
    assert execution.job.provider_job_id == "provider-request-123"
    assert "Sensitive prompt content" not in str(execution.job.input_data)
    assert "Generated response" not in str(execution.job.output_data)


def test_ai_execution_persists_sanitized_failure(db_session: Session) -> None:
    registry = AIProviderRegistry()
    registry.register(FailingProvider())
    service = AIExecutionService(
        db_session,
        Settings(ai_provider="failing-provider", ai_model="provider-model"),
        registry,
    )
    user_id = create_user(db_session, "failure@example.com")

    with pytest.raises(ApplicationError) as error:
        service.execute(
            user_id=user_id,
            job_type="contract_test",
            request=generation_request(),
        )

    assert error.value.code == "AI_GENERATION_FAILED"
    job = service.jobs.list_for_user(user_id)[0]
    assert job.status is AIJobStatus.FAILED
    assert job.error_code == "PROVIDER_TIMEOUT"
    assert job.error_message == "AI generation failed."
    assert job.output_data == {"retryable": True}


def test_unregistered_provider_is_not_faked(db_session: Session) -> None:
    service = AIExecutionService(
        db_session,
        Settings(ai_provider="missing-provider", ai_model="provider-model"),
        AIProviderRegistry(),
    )
    user_id = create_user(db_session, "missing@example.com")

    with pytest.raises(ApplicationError) as error:
        service.execute(
            user_id=user_id,
            job_type="contract_test",
            request=generation_request(),
        )

    assert error.value.code == "AI_PROVIDER_UNAVAILABLE"


def test_provider_registry_rejects_duplicate_names() -> None:
    registry = AIProviderRegistry()
    registry.register(SuccessfulProvider())

    with pytest.raises(ValueError):
        registry.register(SuccessfulProvider())
