from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.creator_progress import CreatorGoalUpdate, CreatorProgressResponse
from app.services.creator_progress import CreatorProgressService

router = APIRouter(prefix="/creator-progress")


@router.get("", response_model=CreatorProgressResponse)
def get_progress(user: CurrentUser, session: DatabaseSession) -> CreatorProgressResponse:
    return CreatorProgressService(session).get(user.id)


@router.patch("/goal", response_model=CreatorProgressResponse)
def update_goal(
    payload: CreatorGoalUpdate, user: CurrentUser, session: DatabaseSession
) -> CreatorProgressResponse:
    return CreatorProgressService(session).update_goal(user.id, payload.monthly_post_target)
