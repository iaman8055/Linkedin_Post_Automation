from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.repositories.base import UserOwnedRepository


class WorkspaceRepository(UserOwnedRepository[Workspace]):
    def __init__(self, session: Session) -> None:
        super().__init__(Workspace, session)

    def list_active(self, user_id: UUID) -> list[Workspace]:
        return list(self.session.scalars(
            select(Workspace).where(
                Workspace.user_id == user_id, Workspace.is_active.is_(True)
            ).order_by(Workspace.is_default.desc(), Workspace.created_at)
        ))

    def default(self, user_id: UUID) -> Workspace | None:
        return self.session.scalar(select(Workspace).where(
            Workspace.user_id == user_id, Workspace.is_default.is_(True)
        ))
