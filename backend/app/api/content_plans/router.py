from uuid import UUID

from fastapi import APIRouter

from app.api.ai.router import ProviderRegistry
from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.content_workflows import (
    ApproveContentPlanRequest,
    ApproveContentPlanResponse,
    ContentPlanListResponse,
    ContentPlanResponse,
    GenerateContentPlanRequest,
    RepurposedPostResponse,
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.content_workflows import ContentWorkflowService

router = APIRouter()


@router.post("/ai/repurpose", response_model=RepurposeResponse)
def repurpose_content(
    payload: RepurposeRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> RepurposeResponse:
    job_id, posts = ContentWorkflowService(session, settings, registry).repurpose(
        user.id, payload
    )
    return RepurposeResponse(
        job_id=job_id,
        posts=[RepurposedPostResponse.model_validate(post, from_attributes=True) for post in posts],
    )


@router.post("/content-plans/generate", response_model=ContentPlanResponse, status_code=201)
def generate_plan(
    payload: GenerateContentPlanRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> ContentPlanResponse:
    _, plan = ContentWorkflowService(session, settings, registry).generate_plan(user.id, payload)
    return ContentPlanResponse.model_validate(plan)


@router.get("/content-plans", response_model=ContentPlanListResponse)
def list_plans(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings,
    registry: ProviderRegistry,
) -> ContentPlanListResponse:
    plans = ContentWorkflowService(session, settings, registry).list_plans(user.id)
    return ContentPlanListResponse(
        items=[ContentPlanResponse.model_validate(plan) for plan in plans]
    )


@router.post("/content-plans/{plan_id}/approve", response_model=ApproveContentPlanResponse)
def approve_plan(
    plan_id: UUID, payload: ApproveContentPlanRequest, user: CurrentUser,
    session: DatabaseSession, settings: AppSettings, registry: ProviderRegistry,
) -> ApproveContentPlanResponse:
    return ContentWorkflowService(session, settings, registry).approve_plan(
        user.id, plan_id, schedule_for_auto_publish=payload.schedule_for_auto_publish
    )
