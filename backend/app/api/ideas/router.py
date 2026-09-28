from uuid import UUID

from fastapi import APIRouter, Query

from app.api.ai.router import ProviderRegistry
from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.content_workflows import (
    ContentIdeaCreate,
    ContentIdeaListResponse,
    ContentIdeaResponse,
    GenerateIdeasRequest,
    GenerateIdeasResponse,
)
from app.schemas.post import PostResponse
from app.services.content_workflows import ContentWorkflowService

router = APIRouter(prefix="/ideas")


@router.post("/generate", response_model=GenerateIdeasResponse)
def generate_ideas(
    payload: GenerateIdeasRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> GenerateIdeasResponse:
    job_id, result = ContentWorkflowService(session, settings, registry).generate_ideas(
        user.id, payload
    )
    return GenerateIdeasResponse(job_id=job_id, ideas=result.ideas)


@router.post("", response_model=ContentIdeaResponse, status_code=201)
def save_idea(
    payload: ContentIdeaCreate, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> ContentIdeaResponse:
    idea = ContentWorkflowService(session, settings, registry).save_idea(user.id, payload)
    return ContentIdeaResponse.model_validate(idea)


@router.get("", response_model=ContentIdeaListResponse)
def list_ideas(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings,
    registry: ProviderRegistry, limit: int = Query(default=50, ge=1, le=100),
) -> ContentIdeaListResponse:
    items, total = ContentWorkflowService(session, settings, registry).list_ideas(user.id)
    return ContentIdeaListResponse(
        items=[ContentIdeaResponse.model_validate(item) for item in items[:limit]], total=total
    )


@router.post("/{idea_id}/create-post", response_model=PostResponse, status_code=201)
def create_post_from_idea(
    idea_id: UUID, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> PostResponse:
    post = ContentWorkflowService(session, settings, registry).create_post_from_idea(
        user.id, idea_id
    )
    return PostResponse.model_validate(post)
