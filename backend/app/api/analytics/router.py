from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsStatusResponse,
    PerformanceInsightsResponse,
    PostAnalyticsResponse,
    SchedulingSuggestionsResponse,
)
from app.services.analytics import AnalyticsService
from app.services.linkedin.client import LinkedInClient

router = APIRouter(prefix="/analytics")


def service(session: DatabaseSession, settings: AppSettings) -> AnalyticsService:
    return AnalyticsService(session, settings, LinkedInClient())


@router.get("/status", response_model=AnalyticsStatusResponse)
def status(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings
) -> AnalyticsStatusResponse:
    connected, permission = service(session, settings).status(user.id)
    return AnalyticsStatusResponse(
        connected=connected,
        permission_granted=permission,
        required_scope=AnalyticsService.required_scope,
        collection_available=connected and permission,
    )


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings
) -> AnalyticsOverviewResponse:
    return service(session, settings).overview(user.id)


@router.get("/insights", response_model=PerformanceInsightsResponse)
def insights(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings
) -> PerformanceInsightsResponse:
    return service(session, settings).performance_insights(user.id)


@router.get("/scheduling-suggestions", response_model=SchedulingSuggestionsResponse)
def scheduling_suggestions(
    user: CurrentUser, session: DatabaseSession, settings: AppSettings
) -> SchedulingSuggestionsResponse:
    return service(session, settings).scheduling_suggestions(user.id)


@router.post("/posts/{post_id}/refresh", response_model=PostAnalyticsResponse)
def refresh_post(
    post_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> PostAnalyticsResponse:
    snapshot = service(session, settings).collect(user.id, post_id)
    return PostAnalyticsResponse.model_validate(snapshot)


@router.get("/posts/{post_id}/history", response_model=list[PostAnalyticsResponse])
def post_history(
    post_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> list[PostAnalyticsResponse]:
    snapshots = service(session, settings).history(user.id, post_id)
    return [PostAnalyticsResponse.model_validate(item) for item in snapshots]
