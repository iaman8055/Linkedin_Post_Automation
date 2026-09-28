from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.user_settings import UserSettings
from app.models.workspace import Workspace
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.workspaces = WorkspaceRepository(session)

    def ensure_default(self, user_id: UUID) -> Workspace:
        workspace = self.workspaces.default(user_id)
        if workspace is None:
            workspace = self.workspaces.create_for_user(
                user_id, name="Personal", kind="personal", is_default=True, is_active=True
            )
        settings = self.session.query(UserSettings).filter_by(user_id=user_id).one_or_none()
        if settings is None:
            settings = UserSettings(user_id=user_id, active_workspace_id=workspace.id)
            self.session.add(settings)
        elif settings.active_workspace_id is None:
            settings.active_workspace_id = workspace.id
        self.session.flush()
        return workspace

    def active(self, user_id: UUID) -> Workspace:
        default = self.ensure_default(user_id)
        settings = self.session.query(UserSettings).filter_by(user_id=user_id).one()
        workspace = (
            self.workspaces.get_for_user(settings.active_workspace_id, user_id)
            if settings.active_workspace_id is not None else None
        )
        return workspace if workspace is not None and workspace.is_active else default

    def list(self, user_id: UUID) -> tuple[list[Workspace], UUID]:
        active = self.active(user_id)
        self.session.commit()
        return self.workspaces.list_active(user_id), active.id

    def create(self, user_id: UUID, payload: WorkspaceCreate) -> Workspace:
        self.ensure_default(user_id)
        workspace = self.workspaces.create_for_user(
            user_id, name=payload.name.strip(), kind=payload.kind,
            is_default=False, is_active=True,
        )
        self.session.commit()
        self.session.refresh(workspace)
        return workspace

    def activate(self, user_id: UUID, workspace_id: UUID) -> Workspace:
        workspace = self.workspaces.get_for_user(workspace_id, user_id)
        if workspace is None or not workspace.is_active:
            raise ApplicationError("WORKSPACE_NOT_FOUND", "Workspace not found.", 404)
        self.ensure_default(user_id)
        settings = self.session.query(UserSettings).filter_by(user_id=user_id).one()
        settings.active_workspace_id = workspace.id
        self.session.commit()
        return workspace

    def update(
        self, user_id: UUID, workspace_id: UUID, payload: WorkspaceUpdate
    ) -> Workspace:
        workspace = self.workspaces.get_for_user(workspace_id, user_id)
        if workspace is None:
            raise ApplicationError("WORKSPACE_NOT_FOUND", "Workspace not found.", 404)
        if payload.name is not None:
            workspace.name = payload.name.strip()
        if payload.is_active is False:
            if workspace.is_default or self.active(user_id).id == workspace.id:
                raise ApplicationError(
                    "WORKSPACE_CANNOT_ARCHIVE",
                    "Default or active workspace cannot be archived.",
                    409,
                )
            workspace.is_active = False
        self.session.commit()
        self.session.refresh(workspace)
        return workspace
