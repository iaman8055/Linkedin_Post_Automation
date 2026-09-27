from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.models.enums import PostStatus
from app.schemas.post import PostCreate, PostListResponse, PostResponse, PostUpdate
from app.schemas.quality import QualityCheckResponse
from app.services.ai.quality_checker import QualityChecker
from app.services.ai.registry import AIProviderRegistry, create_provider_registry
from app.services.posts import PostService

router = APIRouter(prefix="/posts")


def get_post_service(session: DatabaseSession) -> PostService:
    return PostService(session)


PostServiceDependency = Annotated[PostService, Depends(get_post_service)]


def get_quality_registry(settings: AppSettings) -> AIProviderRegistry:
    return create_provider_registry(settings)


QualityRegistry = Annotated[AIProviderRegistry, Depends(get_quality_registry)]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate, user: CurrentUser, service: PostServiceDependency
) -> PostResponse:
    return PostResponse.model_validate(service.create(user.id, payload))


@router.get("", response_model=PostListResponse)
def list_posts(
    user: CurrentUser,
    service: PostServiceDependency,
    post_status: Annotated[PostStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PostListResponse:
    posts, total = service.list(
        user.id, status=post_status, search=search, offset=offset, limit=limit
    )
    return PostListResponse(items=posts, total=total, offset=offset, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: UUID, user: CurrentUser, service: PostServiceDependency) -> PostResponse:
    return PostResponse.model_validate(service.get(user.id, post_id))


@router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: UUID, payload: PostUpdate, user: CurrentUser, service: PostServiceDependency
) -> PostResponse:
    return PostResponse.model_validate(service.update(user.id, post_id, payload))


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: UUID, user: CurrentUser, service: PostServiceDependency) -> Response:
    service.delete(user.id, post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{post_id}/approve", response_model=PostResponse)
def approve_post(
    post_id: UUID, user: CurrentUser, service: PostServiceDependency
) -> PostResponse:
    return PostResponse.model_validate(service.approve(user.id, post_id))


@router.post("/{post_id}/return-to-draft", response_model=PostResponse)
def return_post_to_draft(
    post_id: UUID, user: CurrentUser, service: PostServiceDependency
) -> PostResponse:
    return PostResponse.model_validate(service.return_to_draft(user.id, post_id))


@router.post("/{post_id}/quality-check", response_model=QualityCheckResponse)
def quality_check(
    post_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
    registry: QualityRegistry,
) -> QualityCheckResponse:
    return QualityChecker(session, settings, registry).check(user.id, post_id)
