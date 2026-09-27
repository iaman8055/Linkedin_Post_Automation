from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.user import User
from app.schemas.writing_profile import WritingProfileCreate, WritingProfileUpdate
from app.services.writing_profiles import WritingProfileService


def make_user(session: Session, email: str) -> User:
    user = User(email=email, password_hash="hashed", display_name="Profile User")
    session.add(user)
    session.commit()
    return user


def test_profile_defaults_and_delete_reassignment(db_session: Session) -> None:
    owner = make_user(db_session, "profile-owner@example.com")
    service = WritingProfileService(db_session)
    first = service.create(
        owner.id,
        WritingProfileCreate(
            name="Professional voice",
            tone="Direct and thoughtful",
            preferred_vocabulary=["practical", "Practical", " evidence-led "],
        ),
    )
    second = service.create(
        owner.id, WritingProfileCreate(name="Conversational", is_default=True)
    )

    db_session.refresh(first)
    assert first.is_default is False
    assert second.is_default is True
    assert first.preferred_vocabulary == ["practical", "evidence-led"]

    service.delete(owner.id, second.id)
    db_session.refresh(first)
    assert first.is_default is True


def test_profile_ownership_and_default_guard(db_session: Session) -> None:
    owner = make_user(db_session, "profile-one@example.com")
    other = make_user(db_session, "profile-two@example.com")
    service = WritingProfileService(db_session)
    profile = service.create(owner.id, WritingProfileCreate(name="Default"))

    with pytest.raises(ApplicationError) as default_error:
        service.update(
            owner.id, profile.id, WritingProfileUpdate(is_default=False)
        )
    assert default_error.value.code == "DEFAULT_PROFILE_REQUIRED"
    with pytest.raises(ApplicationError) as hidden:
        service.get(other.id, profile.id)
    assert hidden.value.code == "WRITING_PROFILE_NOT_FOUND"
    with pytest.raises(ApplicationError):
        service.get(owner.id, uuid4())
