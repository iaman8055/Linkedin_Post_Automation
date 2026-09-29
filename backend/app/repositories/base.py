from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.user_settings import UserSettings
from app.models.workspace import Workspace


class BaseRepository[ModelT: Base]:
    def __init__(self, model: type[ModelT], session: Session) -> None:
        self.model = model
        self.session = session

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.flush()
        return instance

    def get(self, object_id: UUID) -> ModelT | None:
        return self.session.get(self.model, object_id)

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)
        self.session.flush()


class UserOwnedRepository[ModelT: Base](BaseRepository[ModelT]):
    """Base query helpers that always include the owning user's identifier."""

    def active_workspace_id(self, user_id: UUID) -> UUID:
        settings = self.session.scalar(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        if settings is not None and settings.active_workspace_id is not None:
            workspace = self.session.scalar(
                select(Workspace).where(
                    Workspace.id == settings.active_workspace_id,
                    Workspace.user_id == user_id,
                    Workspace.is_active.is_(True),
                )
            )
            if workspace is not None:
                return workspace.id
        workspace = self.session.scalar(
            select(Workspace).where(
                Workspace.user_id == user_id,
                Workspace.is_default.is_(True),
                Workspace.is_active.is_(True),
            )
        )
        if workspace is None:
            workspace = Workspace(
                user_id=user_id, name="Personal", kind="personal",
                is_default=True, is_active=True,
            )
            self.session.add(workspace)
            self.session.flush()
        if settings is None:
            settings = UserSettings(user_id=user_id, active_workspace_id=workspace.id)
            self.session.add(settings)
        else:
            settings.active_workspace_id = workspace.id
        self.session.flush()
        return workspace.id

    def ownership_filters(self, user_id: UUID) -> list[Any]:
        model: Any = self.model
        filters = [model.user_id == user_id]
        if hasattr(model, "workspace_id"):
            filters.append(or_(
                model.workspace_id == self.active_workspace_id(user_id),
                model.workspace_id.is_(None),
            ))
        return filters

    def get_for_user(self, object_id: UUID, user_id: UUID) -> ModelT | None:
        model: Any = self.model
        statement = select(self.model).where(
            model.id == object_id,
            *self.ownership_filters(user_id),
        )
        return self.session.scalar(statement)

    def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
        statement = (
            select(self.model)
            .where(*self.ownership_filters(user_id))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def create_for_user(self, user_id: UUID, **values: Any) -> ModelT:
        if hasattr(self.model, "workspace_id"):
            values["workspace_id"] = self.active_workspace_id(user_id)
        return self.add(self.model(user_id=user_id, **values))
