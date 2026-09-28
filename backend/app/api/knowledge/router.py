from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemListResponse,
    KnowledgeItemResponse,
    KnowledgeItemUpdate,
)
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge")


@router.get("", response_model=KnowledgeItemListResponse)
def list_items(user: CurrentUser, session: DatabaseSession) -> KnowledgeItemListResponse:
    items, total = KnowledgeService(session).list(user.id)
    return KnowledgeItemListResponse(
        items=[KnowledgeItemResponse.model_validate(item) for item in items], total=total
    )


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: KnowledgeItemCreate, user: CurrentUser, session: DatabaseSession
) -> KnowledgeItemResponse:
    return KnowledgeItemResponse.model_validate(KnowledgeService(session).create(user.id, payload))


@router.patch("/{item_id}", response_model=KnowledgeItemResponse)
def update_item(
    item_id: UUID, payload: KnowledgeItemUpdate, user: CurrentUser, session: DatabaseSession
) -> KnowledgeItemResponse:
    return KnowledgeItemResponse.model_validate(
        KnowledgeService(session).update(user.id, item_id, payload)
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: UUID, user: CurrentUser, session: DatabaseSession) -> Response:
    KnowledgeService(session).delete(user.id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
