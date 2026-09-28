from uuid import UUID

from fastapi import APIRouter

from app.api.ai.router import ProviderRegistry
from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.engagement import (
    CreateExperimentRequest,
    ExperimentComparisonResponse,
    ExperimentResponse,
    GenerateCommentResponsesRequest,
    GenerateCommentResponsesResponse,
)
from app.services.engagement import EngagementService

router = APIRouter()


@router.post("/comments/generate-response", response_model=GenerateCommentResponsesResponse)
def generate_comment_response(
    payload: GenerateCommentResponsesRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> GenerateCommentResponsesResponse:
    service = EngagementService(session, settings, registry)
    job_id, result = service.comment_responses(user.id, payload)
    return GenerateCommentResponsesResponse(
        job_id=job_id, suggestions=result.suggestions, disclaimer=service.comment_disclaimer
    )


@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
def create_experiment(
    payload: CreateExperimentRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> ExperimentResponse:
    _, experiment = EngagementService(session, settings, registry).create_experiment(
        user.id, payload
    )
    return ExperimentResponse.model_validate(experiment)


@router.get("/experiments", response_model=list[ExperimentResponse])
def list_experiments(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings,
    registry: ProviderRegistry,
) -> list[ExperimentResponse]:
    experiments = EngagementService(session, settings, registry).list_experiments(user.id)
    return [ExperimentResponse.model_validate(item) for item in experiments]


@router.get(
    "/experiments/{experiment_id}/comparison",
    response_model=ExperimentComparisonResponse,
)
def compare_experiment(
    experiment_id: UUID, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> ExperimentComparisonResponse:
    return EngagementService(session, settings, registry).compare(user.id, experiment_id)
