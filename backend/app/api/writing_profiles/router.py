from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.ai.router import ProviderRegistry
from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.schemas.writing_profile import (
    AnalyzeWritingStyleRequest,
    AnalyzeWritingStyleResponse,
    WritingProfileCreate,
    WritingProfileListResponse,
    WritingProfileResponse,
    WritingProfileUpdate,
)
from app.services.ai.writing_style_analyzer import WritingStyleAnalyzer
from app.services.writing_profiles import WritingProfileService

router = APIRouter(prefix="/writing-profiles")


@router.post("/analyze", response_model=AnalyzeWritingStyleResponse)
def analyze_style(
    payload: AnalyzeWritingStyleRequest, user: CurrentUser, session: DatabaseSession,
    settings: AppSettings, registry: ProviderRegistry,
) -> AnalyzeWritingStyleResponse:
    return WritingStyleAnalyzer(session, settings, registry).analyze(user.id, payload)


@router.post("", response_model=WritingProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: WritingProfileCreate, user: CurrentUser, session: DatabaseSession
) -> WritingProfileResponse:
    profile = WritingProfileService(session).create(user.id, payload)
    return WritingProfileResponse.model_validate(profile)


@router.get("", response_model=WritingProfileListResponse)
def list_profiles(
    user: CurrentUser,
    session: DatabaseSession,
    limit: int = Query(50, ge=1, le=100),
) -> WritingProfileListResponse:
    profiles, total = WritingProfileService(session).list_profiles(user.id)
    return WritingProfileListResponse(
        items=[WritingProfileResponse.model_validate(item) for item in profiles[:limit]],
        total=total,
    )


@router.get("/{profile_id}", response_model=WritingProfileResponse)
def get_profile(
    profile_id: UUID, user: CurrentUser, session: DatabaseSession
) -> WritingProfileResponse:
    profile = WritingProfileService(session).get(user.id, profile_id)
    return WritingProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=WritingProfileResponse)
def update_profile(
    profile_id: UUID,
    payload: WritingProfileUpdate,
    user: CurrentUser,
    session: DatabaseSession,
) -> WritingProfileResponse:
    profile = WritingProfileService(session).update(user.id, profile_id, payload)
    return WritingProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: UUID, user: CurrentUser, session: DatabaseSession) -> Response:
    WritingProfileService(session).delete(user.id, profile_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
