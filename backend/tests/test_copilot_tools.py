import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.audit_log import AuditLog
from app.models.post import Post
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.workspace import Workspace
from app.repositories.post import PostRepository
from app.services.ai.tools import CopilotToolCall, CopilotToolService


def workspace_user(db_session: Session) -> tuple[User, Workspace, Workspace, UserSettings]:
    user = User(email="copilot@example.com", password_hash="hashed", display_name="Copilot")
    db_session.add(user)
    db_session.flush()
    personal = Workspace(
        user_id=user.id, name="Personal", kind="personal", is_default=True, is_active=True
    )
    client = Workspace(user_id=user.id, name="Client", kind="client", is_active=True)
    db_session.add_all([personal, client])
    db_session.flush()
    settings = UserSettings(user_id=user.id, active_workspace_id=personal.id)
    db_session.add(settings)
    db_session.commit()
    return user, personal, client, settings


def test_read_tool_only_returns_active_workspace_data(db_session: Session) -> None:
    user, _, client, settings = workspace_user(db_session)
    posts = PostRepository(db_session)
    posts.create_for_user(user.id, title="Personal post", content="Personal content")
    db_session.commit()
    settings.active_workspace_id = client.id
    db_session.commit()
    client_post = posts.create_for_user(user.id, title="Client post", content="Client content")
    db_session.commit()

    result = CopilotToolService(db_session).execute(
        user.id, CopilotToolCall(name="get_recent_posts", arguments={"limit": 10})
    )

    assert result.status == "completed"
    assert result.workspace_id == str(client.id)
    assert isinstance(result.output, list)
    assert [item["id"] for item in result.output] == [str(client_post.id)]


def test_write_tool_requires_confirmation_and_only_creates_a_draft(
    db_session: Session,
) -> None:
    user, _, client, settings = workspace_user(db_session)
    settings.active_workspace_id = client.id
    db_session.commit()
    service = CopilotToolService(db_session)
    call = CopilotToolCall(
        name="create_draft",
        arguments={"title": "Review me", "content": "This must remain a draft."},
    )

    proposal = service.execute(user.id, call)
    count_before = db_session.scalar(select(func.count()).select_from(Post))
    completed = service.execute(user.id, call, confirmed=True)
    created = db_session.scalar(select(Post).where(Post.title == "Review me"))

    assert proposal.status == "confirmation_required"
    assert count_before == 0
    assert completed.status == "completed"
    assert created is not None
    assert created.status.value == "DRAFT"
    assert created.workspace_id == client.id
    audits = list(db_session.scalars(select(AuditLog).order_by(AuditLog.created_at)))
    assert [item.details["outcome"] for item in audits] == [
        "confirmation_required", "completed"
    ]
    assert all("content" not in item.details for item in audits)


def test_unregistered_or_publish_tool_is_rejected(db_session: Session) -> None:
    user, _, _, _ = workspace_user(db_session)

    with pytest.raises(ApplicationError) as exc_info:
        CopilotToolService(db_session).execute(
            user.id, CopilotToolCall(name="publish_post", arguments={})
        )

    assert exc_info.value.code == "COPILOT_TOOL_NOT_ALLOWED"


def test_tool_arguments_forbid_unexpected_fields(db_session: Session) -> None:
    user, _, _, _ = workspace_user(db_session)

    with pytest.raises(ApplicationError) as exc_info:
        CopilotToolService(db_session).execute(
            user.id,
            CopilotToolCall(name="get_recent_posts", arguments={"limit": 5, "user_id": "other"}),
        )

    assert exc_info.value.code == "COPILOT_TOOL_INPUT_INVALID"
