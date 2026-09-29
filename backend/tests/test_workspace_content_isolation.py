from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.workspace import Workspace
from app.repositories.post import PostRepository


def test_repository_writes_to_active_workspace_and_isolates_reads(
    db_session: Session,
) -> None:
    user = User(email="workspace-content@example.com", password_hash="hashed", display_name="Owner")
    db_session.add(user)
    db_session.flush()
    first = Workspace(user_id=user.id, name="Personal", kind="personal", is_default=True)
    second = Workspace(user_id=user.id, name="Client", kind="client")
    db_session.add_all([first, second])
    db_session.flush()
    settings = UserSettings(user_id=user.id, active_workspace_id=first.id)
    db_session.add(settings)
    db_session.commit()
    repository = PostRepository(db_session)

    personal_post = repository.create_for_user(
        user.id, title="Personal", content="Personal workspace", language="English"
    )
    db_session.commit()
    settings.active_workspace_id = second.id
    db_session.commit()
    client_post = repository.create_for_user(
        user.id, title="Client", content="Client workspace", language="English"
    )
    db_session.commit()

    visible, total = repository.list_filtered_for_user(user.id)

    assert personal_post.workspace_id == first.id
    assert client_post.workspace_id == second.id
    assert total == 1
    assert [post.id for post in visible] == [client_post.id]
    assert repository.get_for_user(personal_post.id, user.id) is None


def test_legacy_null_workspace_record_remains_available_during_backfill_stage(
    db_session: Session,
) -> None:
    user = User(email="legacy-content@example.com", password_hash="hashed", display_name="Legacy")
    db_session.add(user)
    db_session.flush()
    legacy = Post(user_id=user.id, title="Legacy", content="Before migration")
    db_session.add(legacy)
    db_session.commit()

    assert PostRepository(db_session).get_for_user(legacy.id, user.id) is not None
