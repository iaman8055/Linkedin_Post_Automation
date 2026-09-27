from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.research_source import ResearchSource
from app.repositories.base import UserOwnedRepository


class ResearchSourceRepository(UserOwnedRepository[ResearchSource]):
    def __init__(self, session: Session) -> None:
        super().__init__(ResearchSource, session)

    def list_recent(
        self, user_id: UUID, *, offset: int, limit: int
    ) -> tuple[list[ResearchSource], int]:
        filters = (ResearchSource.user_id == user_id,)
        total = self.session.scalar(
            select(func.count()).select_from(ResearchSource).where(*filters)
        ) or 0
        statement = select(ResearchSource).where(*filters).order_by(
            ResearchSource.retrieved_at.desc(), ResearchSource.id.desc()
        ).offset(offset).limit(limit)
        return list(self.session.scalars(statement)), total
