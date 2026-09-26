from sqlalchemy.orm import Session

from app.models import User
from app.repositories.post import PostRepository


def test_user_owned_repository_prevents_cross_user_reads(db_session: Session) -> None:
    owner = User(email="owner@example.com", password_hash="hashed", display_name="Owner")
    other_user = User(email="other@example.com", password_hash="hashed", display_name="Other")
    db_session.add_all([owner, other_user])
    db_session.flush()

    repository = PostRepository(db_session)
    post = repository.create_for_user(owner.id, content="Private content")

    assert repository.get_for_user(post.id, owner.id) == post
    assert repository.get_for_user(post.id, other_user.id) is None
    assert repository.list_for_user(other_user.id) == []

