from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import PostStatus
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.services.posts import PostService


def create_user(session: Session, email: str) -> User:
    user = User(email=email, password_hash="hashed", display_name="Post Author")
    session.add(user)
    session.commit()
    return user


def test_post_crud_is_user_scoped_and_fingerprinted(db_session: Session) -> None:
    owner = create_user(db_session, "post-owner@example.com")
    other = create_user(db_session, "post-other@example.com")
    service = PostService(db_session)

    post = service.create(
        owner.id,
        PostCreate(title="  First draft  ", content="A useful draft.", language="English"),
    )
    assert post.status == PostStatus.DRAFT
    assert post.title == "First draft"
    assert len(post.content_fingerprint or "") == 64

    items, total = service.list(
        owner.id, status=PostStatus.DRAFT, search="useful", offset=0, limit=20
    )
    assert items == [post]
    assert total == 1

    with pytest.raises(ApplicationError) as not_found:
        service.get(other.id, post.id)
    assert not_found.value.code == "POST_NOT_FOUND"

    old_fingerprint = post.content_fingerprint
    updated = service.update(owner.id, post.id, PostUpdate(content="An improved draft."))
    assert updated.content == "An improved draft."
    assert updated.content_fingerprint != old_fingerprint

    service.delete(owner.id, post.id)
    with pytest.raises(ApplicationError):
        service.get(owner.id, post.id)


def test_only_drafts_can_be_edited_or_deleted(db_session: Session) -> None:
    user = create_user(db_session, "locked-post@example.com")
    service = PostService(db_session)
    post = service.create(user.id, PostCreate(content="Already approved."))
    post.status = PostStatus.APPROVED
    db_session.commit()

    with pytest.raises(ApplicationError) as edit_error:
        service.update(user.id, post.id, PostUpdate(content="Changed"))
    assert edit_error.value.code == "POST_NOT_EDITABLE"

    with pytest.raises(ApplicationError) as delete_error:
        service.delete(user.id, post.id)
    assert delete_error.value.code == "POST_NOT_DELETABLE"


def test_missing_post_is_not_leaked(db_session: Session) -> None:
    user = create_user(db_session, "missing-post@example.com")
    with pytest.raises(ApplicationError) as error:
        PostService(db_session).get(user.id, uuid4())
    assert error.value.status_code == 404


def test_post_approval_round_trip(db_session: Session) -> None:
    user = create_user(db_session, "approve-post@example.com")
    service = PostService(db_session)
    post = service.create(user.id, PostCreate(content="Ready for review."))

    approved = service.approve(user.id, post.id)
    assert approved.status is PostStatus.APPROVED
    assert approved.approved_at is not None
    draft = service.return_to_draft(user.id, post.id)
    assert draft.status is PostStatus.DRAFT
    assert draft.approved_at is None
