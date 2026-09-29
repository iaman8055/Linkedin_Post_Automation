from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.content_idea import ContentIdea
from app.repositories.base import UserOwnedRepository


class ContentIdeaRepository(UserOwnedRepository[ContentIdea]):
    def __init__(self, session: Session) -> None:
        super().__init__(ContentIdea, session)

    def list_recent(self, user_id: UUID, *, limit: int = 50) -> tuple[list[ContentIdea], int]:
        filters = self.ownership_filters(user_id)
        statement = (
            select(ContentIdea).where(*filters)
            .order_by(ContentIdea.created_at.desc()).limit(limit)
        )
        count = select(func.count()).select_from(ContentIdea).where(*filters)
        return list(self.session.scalars(statement)), self.session.scalar(count) or 0
