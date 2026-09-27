from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.ai import (
    AIProviderStatusResponse,
    GeneratePostsRequest,
    GeneratePostsResponse,
)
from app.schemas.post import PostResponse
from app.services.ai.content_generator import ContentGenerator
from app.services.ai.registry import AIProviderRegistry, create_provider_registry

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
