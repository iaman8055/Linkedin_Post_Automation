from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.knowledge_item import KnowledgeItem
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate


class KnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.items = KnowledgeItemRepository(session)

    def create(self, user_id: UUID, payload: KnowledgeItemCreate) -> KnowledgeItem:
        item = self.items.create_for_user(user_id, **payload.model_dump())
        self.session.commit()
        self.session.refresh(item)
        return item

    def list(self, user_id: UUID) -> tuple[list[KnowledgeItem], int]:
        return self.items.list_with_total(user_id)

    def get(self, user_id: UUID, item_id: UUID) -> KnowledgeItem:
        item = self.items.get_for_user(item_id, user_id)
        if item is None:
            raise ApplicationError("KNOWLEDGE_ITEM_NOT_FOUND", "Knowledge item not found.", 404)
        return item

    def update(
        self, user_id: UUID, item_id: UUID, payload: KnowledgeItemUpdate
    ) -> KnowledgeItem:
        item = self.get(user_id, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value.strip() if isinstance(value, str) else value)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, user_id: UUID, item_id: UUID) -> None:
        self.items.delete(self.get(user_id, item_id))
        self.session.commit()
