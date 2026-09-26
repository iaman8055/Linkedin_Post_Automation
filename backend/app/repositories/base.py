from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base


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

    def get_for_user(self, object_id: UUID, user_id: UUID) -> ModelT | None:
        model: Any = self.model
        statement = select(self.model).where(
            model.id == object_id,
            model.user_id == user_id,
        )
        return self.session.scalar(statement)

    def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 50) -> list[ModelT]:
        model: Any = self.model
        statement = (
            select(self.model)
            .where(model.user_id == user_id)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def create_for_user(self, user_id: UUID, **values: Any) -> ModelT:
        return self.add(self.model(user_id=user_id, **values))
