import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.workspaces import WorkspaceService


def test_workspace_default_creation_and_switching(db_session: Session) -> None:
    user = User(email="workspace@example.com", password_hash="hashed", display_name="Owner")
    db_session.add(user)
    db_session.commit()
    service = WorkspaceService(db_session)

    personal = service.active(user.id)
    client = service.create(user.id, WorkspaceCreate(name="Client A", kind="client"))
    activated = service.activate(user.id, client.id)
    items, active_id = service.list(user.id)

    assert personal.is_default is True
    assert activated.id == client.id
    assert active_id == client.id
    assert {item.name for item in items} == {"Personal", "Client A"}
    with pytest.raises(ApplicationError) as protected:
        service.update(user.id, client.id, WorkspaceUpdate(is_active=False))
    assert protected.value.code == "WORKSPACE_CANNOT_ARCHIVE"
