from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspaces import WorkspaceService

router = APIRouter(prefix="/workspaces")


@router.get("", response_model=WorkspaceListResponse)
def list_workspaces(user: CurrentUser, session: DatabaseSession) -> WorkspaceListResponse:
    items, active_id = WorkspaceService(session).list(user.id)
    return WorkspaceListResponse(
        items=[WorkspaceResponse.model_validate(item).model_copy(
            update={"is_current": item.id == active_id}
        ) for item in items], active_workspace_id=active_id,
    )


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    payload: WorkspaceCreate, user: CurrentUser, session: DatabaseSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(WorkspaceService(session).create(user.id, payload))


@router.post("/{workspace_id}/activate", response_model=WorkspaceResponse)
def activate_workspace(
    workspace_id: UUID, user: CurrentUser, session: DatabaseSession
) -> WorkspaceResponse:
    workspace = WorkspaceService(session).activate(user.id, workspace_id)
    return WorkspaceResponse.model_validate(workspace).model_copy(update={"is_current": True})


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(
    workspace_id: UUID, payload: WorkspaceUpdate, user: CurrentUser,
    session: DatabaseSession,
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        WorkspaceService(session).update(user.id, workspace_id, payload)
    )
