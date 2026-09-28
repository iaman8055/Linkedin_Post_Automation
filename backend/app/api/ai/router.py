from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.ai import (
    AIProviderStatusResponse,
    AssistPostRequest,
    AssistPostResponse,
    GeneratePostsRequest,
    GeneratePostsResponse,
)
from app.schemas.content_intelligence import (
    GenerateHooksRequest,
    GenerateHooksResponse,
    PostScoreResponse,
)
from app.schemas.post import PostResponse
from app.services.ai.content_generator import ContentGenerator
from app.services.ai.content_intelligence import ContentIntelligenceService
from app.services.ai.registry import AIProviderRegistry, create_provider_registry
from app.services.ai.writing_assistant import WritingAssistant

router = APIRouter(prefix="/ai")


def get_provider_registry(settings: AppSettings) -> AIProviderRegistry:
    return create_provider_registry(settings)


ProviderRegistry = Annotated[AIProviderRegistry, Depends(get_provider_registry)]


@router.get("/status", response_model=AIProviderStatusResponse)
def provider_status(
    _: CurrentUser, settings: AppSettings, registry: ProviderRegistry
) -> AIProviderStatusResponse:
    selected = settings.ai_provider.strip().lower() if settings.ai_provider else None
    installed = selected is not None and registry.get(selected) is not None
    return AIProviderStatusResponse(
        selected_provider=selected,
        selected_model=settings.ai_model,
        provider_installed=installed,
        registered_providers=registry.names(),
    )


@router.post("/posts/generate", response_model=GeneratePostsResponse)
def generate_posts(
    payload: GeneratePostsRequest,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
    registry: ProviderRegistry,
) -> GeneratePostsResponse:
    generator = ContentGenerator(session, settings, registry)
    job_id, posts = generator.generate_posts(user.id, payload)
    return GeneratePostsResponse(
        job_id=job_id,
        posts=[PostResponse.model_validate(post) for post in posts],
    )


@router.post("/posts/{post_id}/assist", response_model=AssistPostResponse)
def assist_post(
    post_id: UUID,
    payload: AssistPostRequest,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
    registry: ProviderRegistry,
) -> AssistPostResponse:
    job_id, content = WritingAssistant(session, settings, registry).assist(
        user.id, post_id, payload
    )
    return AssistPostResponse(job_id=job_id, action=payload.action, content=content)


@router.post("/posts/{post_id}/score", response_model=PostScoreResponse)
def score_post(
    post_id: UUID, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> PostScoreResponse:
    return ContentIntelligenceService(session, settings, registry).score_post(user.id, post_id)


@router.post("/hooks/generate", response_model=GenerateHooksResponse)
def generate_hooks(
    payload: GenerateHooksRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> GenerateHooksResponse:
    job_id, result = ContentIntelligenceService(session, settings, registry).generate_hooks(
        user.id, payload
    )
    return GenerateHooksResponse(job_id=job_id, hooks=result.hooks)
