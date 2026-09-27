from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.research import (
    ResearchProviderStatusResponse,
    ResearchSearchRequest,
    ResearchSearchResponse,
    ResearchSourceListResponse,
    ResearchSourceResponse,
)
from app.services.research.registry import create_research_provider
from app.services.research.service import ResearchService

router = APIRouter(prefix="/research")


@router.get("/status", response_model=ResearchProviderStatusResponse)
def provider_status(user: CurrentUser, settings: AppSettings) -> ResearchProviderStatusResponse:
    del user
    selected = settings.research_provider.strip().lower() if settings.research_provider else None
    return ResearchProviderStatusResponse(
        selected_provider=selected,
        configured=create_research_provider(settings) is not None,
    )


@router.post("/search", response_model=ResearchSearchResponse)
def search(
    payload: ResearchSearchRequest,
    user: CurrentUser,
    session: DatabaseSession,
    settings: AppSettings,
) -> ResearchSearchResponse:
    answer, provider, sources = ResearchService(
        session, create_research_provider(settings)
    ).search(user.id, payload)
    return ResearchSearchResponse(
        answer=answer,
        provider=provider,
        sources=[ResearchSourceResponse.model_validate(source) for source in sources],
    )


@router.get("/sources", response_model=ResearchSourceListResponse)
def list_sources(
    user: CurrentUser,
    session: DatabaseSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ResearchSourceListResponse:
    sources, total = ResearchService(session, None).list_sources(
        user.id, offset=offset, limit=limit
    )
    return ResearchSourceListResponse(
        items=[ResearchSourceResponse.model_validate(source) for source in sources],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: UUID, user: CurrentUser, session: DatabaseSession
) -> Response:
    ResearchService(session, None).delete(user.id, source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
