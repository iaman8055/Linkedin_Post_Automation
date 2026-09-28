from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.user import User
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate
from app.services.knowledge import KnowledgeService


def make_user(session: Session, email: str) -> User:
    user = User(email=email, password_hash="hashed", display_name="Knowledge User")
    session.add(user)
    session.commit()
    return user


def test_knowledge_items_are_private_and_owner_scoped(db_session: Session) -> None:
    owner = make_user(db_session, "knowledge-owner@example.com")
    other = make_user(db_session, "knowledge-other@example.com")
    service = KnowledgeService(db_session)
    item = service.create(owner.id, KnowledgeItemCreate(
        category="project", title="AI assistant", content="Built with FastAPI and React."
    ))

    assert item.is_private is True
    assert service.list(owner.id)[1] == 1
    assert service.update(
        owner.id, item.id, KnowledgeItemUpdate(tags=["Python"])
    ).tags == ["Python"]
    with pytest.raises(ApplicationError) as hidden:
        service.get(other.id, item.id)
    assert hidden.value.code == "KNOWLEDGE_ITEM_NOT_FOUND"
    with pytest.raises(ApplicationError):
        service.get(owner.id, uuid4())
