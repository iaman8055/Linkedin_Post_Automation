from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.search import GlobalSearchFilters, GlobalSearchResponse
from app.services.search import GlobalSearchService

router = APIRouter(prefix="/search")


@router.get("", response_model=GlobalSearchResponse)
def global_search(
    user: CurrentUser,
    session: DatabaseSession,
    query: Annotated[str | None, Query(alias="q", max_length=200)] = None,
    entity_type: Literal["all", "post", "idea", "knowledge", "template"] = "all",
    search_status: Annotated[str | None, Query(alias="status", max_length=32)] = None,
    topic: Annotated[str | None, Query(max_length=160)] = None,
    tag: Annotated[str | None, Query(max_length=80)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> GlobalSearchResponse:
    filters = GlobalSearchFilters(
        query=query, entity_type=entity_type, status=search_status, topic=topic,
        tag=tag, date_from=date_from, date_to=date_to, limit=limit,
    )
    return GlobalSearchService(session).search(user.id, filters)
