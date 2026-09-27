from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import TemplateStatus
from app.models.user import User
from app.schemas.template import TemplateCreate, TemplateUpdate
from app.services.templates import TemplateService


def user(session: Session, email: str) -> User:
    instance = User(email=email, password_hash="hashed", display_name="Template User")
    session.add(instance)
    session.commit()
    return instance


def test_template_crud_extracts_and_renders_placeholders(db_session: Session) -> None:
    owner = user(db_session, "template-owner@example.com")
    service = TemplateService(db_session)
    template = service.create(
        owner.id,
        TemplateCreate(
            name="Insight post",
            description="A reusable structure",
            body="HOOK: {{topic}}\n\nINSIGHT: {{insight}}\n\nCTA: What do you think?",
        ),
    )

    assert template.placeholders == ["topic", "insight"]
    assert service.render(
        owner.id, template.id, {"topic": "AI agents", "insight": "Start with evaluation."}
    ).startswith("HOOK: AI agents")

    updated = service.update(
        owner.id, template.id, TemplateUpdate(body="A post about {{subject}}.")
    )
    assert updated.placeholders == ["subject"]
    archived = service.set_status(owner.id, template.id, TemplateStatus.ARCHIVED)
    assert archived.status is TemplateStatus.ARCHIVED
    with pytest.raises(ApplicationError) as archived_error:
        service.render(owner.id, template.id, {"subject": "APIs"})
    assert archived_error.value.code == "TEMPLATE_ARCHIVED"


def test_template_validation_and_ownership(db_session: Session) -> None:
    owner = user(db_session, "template-one@example.com")
    other = user(db_session, "template-two@example.com")
    service = TemplateService(db_session)

    with pytest.raises(ApplicationError) as syntax:
        service.create(owner.id, TemplateCreate(name="Broken", body="Hello {{not valid}}"))
    assert syntax.value.code == "TEMPLATE_SYNTAX_INVALID"

    template = service.create(
        owner.id, TemplateCreate(name="Simple", body="Hello {{audience}}")
    )
    with pytest.raises(ApplicationError) as missing:
        service.render(owner.id, template.id, {})
    assert missing.value.code == "TEMPLATE_VALUES_MISSING"
    with pytest.raises(ApplicationError) as hidden:
        service.get(other.id, template.id)
    assert hidden.value.code == "TEMPLATE_NOT_FOUND"
    with pytest.raises(ApplicationError):
        service.get(owner.id, uuid4())
