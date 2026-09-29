from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.knowledge_item import KnowledgeItem
from app.repositories.base import UserOwnedRepository


class KnowledgeItemRepository(UserOwnedRepository[KnowledgeItem]):
    def __init__(self, session: Session) -> None:
        super().__init__(KnowledgeItem, session)

    def list_with_total(self, user_id: UUID) -> tuple[list[KnowledgeItem], int]:
        filters = tuple(self.ownership_filters(user_id))
        statement = select(KnowledgeItem).where(*filters).order_by(
            KnowledgeItem.updated_at.desc()
        )
        count = select(func.count()).select_from(KnowledgeItem).where(*filters)
        return list(self.session.scalars(statement)), self.session.scalar(count) or 0
