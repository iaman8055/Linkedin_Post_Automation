from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models.enums import CampaignStatus
from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignTransitionRequest,
    CampaignUpdate,
)
from app.schemas.post import PostListResponse
from app.services.campaigns import CampaignService

router = APIRouter(prefix="/campaigns")


def get_campaign_service(session: DatabaseSession) -> CampaignService:
    return CampaignService(session)


CampaignServiceDependency = Annotated[CampaignService, Depends(get_campaign_service)]


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignCreate, user: CurrentUser, service: CampaignServiceDependency
) -> CampaignResponse:
    return service.to_response(service.create(user.id, payload))


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    user: CurrentUser,
    service: CampaignServiceDependency,
    campaign_status: Annotated[CampaignStatus | None, Query(alias="status")] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CampaignListResponse:
    campaigns, total = service.list(
        user.id, status=campaign_status, offset=offset, limit=limit
    )
    return CampaignListResponse(
        items=[service.to_response(campaign) for campaign in campaigns],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: UUID, user: CurrentUser, service: CampaignServiceDependency
) -> CampaignResponse:
    return service.to_response(service.get(user.id, campaign_id))


@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    user: CurrentUser,
    service: CampaignServiceDependency,
) -> CampaignResponse:
    return service.to_response(service.update(user.id, campaign_id, payload))


@router.post("/{campaign_id}/transition", response_model=CampaignResponse)
def transition_campaign(
    campaign_id: UUID,
    payload: CampaignTransitionRequest,
    user: CurrentUser,
    service: CampaignServiceDependency,
) -> CampaignResponse:
    return service.to_response(service.transition(user.id, campaign_id, payload.status))


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: UUID, user: CurrentUser, service: CampaignServiceDependency
) -> Response:
    service.delete(user.id, campaign_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{campaign_id}/posts", response_model=PostListResponse)
def list_campaign_posts(
    campaign_id: UUID,
    user: CurrentUser,
    service: CampaignServiceDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PostListResponse:
    service.get(user.id, campaign_id)
    posts, total = service.posts.list_for_campaign(
        user.id, campaign_id, offset=offset, limit=limit
    )
    return PostListResponse(items=posts, total=total, offset=offset, limit=limit)


@router.post("/{campaign_id}/posts/{post_id}", response_model=CampaignResponse)
def add_campaign_post(
    campaign_id: UUID,
    post_id: UUID,
    user: CurrentUser,
    service: CampaignServiceDependency,
) -> CampaignResponse:
    return service.to_response(service.add_post(user.id, campaign_id, post_id))


@router.delete("/{campaign_id}/posts/{post_id}", response_model=CampaignResponse)
def remove_campaign_post(
    campaign_id: UUID,
    post_id: UUID,
    user: CurrentUser,
    service: CampaignServiceDependency,
) -> CampaignResponse:
    return service.to_response(service.remove_post(user.id, campaign_id, post_id))
