from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.copilot import AICopilotAction
from app.models.post import Post
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.workspace import Workspace
from app.schemas.copilot import SendCopilotMessageRequest
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.copilot import CopilotService
from app.services.ai.registry import AIProviderRegistry


class CopilotProvider:
    name = "copilot-test"

    def __init__(self, *, propose_draft: bool = False) -> None:
        self.propose_draft = propose_draft

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        proposed = None
        if self.propose_draft:
            proposed = {
                "tool_name": "create_draft",
                "arguments": {
                    "title": "AI agents lesson",
                    "content": "A reviewable AI agents draft.",
                    "language": "English",
                },
            }
        output = {
            "answer": "Your available posts support a practical AI agents follow-up.",
            "evidence": [{"label": "Available posts", "value": "1 workspace post"}],
            "suggested_action": "Review a new draft.",
            "proposed_action": proposed,
        }
        return AIGenerationResult(
            text="structured", provider=self.name, model=request.model,
            structured_output=output,
        )


def setup_copilot(
    db_session: Session, *, propose_draft: bool = False
) -> tuple[User, Workspace, Workspace, UserSettings, CopilotService]:
    user = User(email="copilot-service@example.com", password_hash="hashed", display_name="Owner")
    db_session.add(user)
    db_session.flush()
    personal = Workspace(
        user_id=user.id, name="Personal", kind="personal", is_default=True, is_active=True
    )
    client = Workspace(user_id=user.id, name="Client", kind="client", is_active=True)
    db_session.add_all([personal, client])
    db_session.flush()
    settings_row = UserSettings(user_id=user.id, active_workspace_id=personal.id)
    db_session.add(settings_row)
    db_session.commit()
    registry = AIProviderRegistry()
    registry.register(CopilotProvider(propose_draft=propose_draft))
    settings = Settings(ai_provider="copilot-test", ai_model="test-model")
    return user, personal, client, settings_row, CopilotService(db_session, settings, registry)


def test_copilot_persists_grounded_conversation_in_active_workspace(
    db_session: Session,
) -> None:
    user, personal, client, settings, service = setup_copilot(db_session)
    conversation = service.create_conversation(user.id, "New conversation")
    loaded, assistant, action = service.send_message(
        user.id, conversation.id,
        SendCopilotMessageRequest(content="What should I post this week?"),
    )

    assert conversation.workspace_id == personal.id
    assert loaded.title == "What should I post this week?"
    assert [message.role for message in loaded.messages] == ["user", "assistant"]
    assert assistant.evidence[0]["value"] == "1 workspace post"
    assert action is None

    settings.active_workspace_id = client.id
    db_session.commit()
    with pytest.raises(ApplicationError) as exc_info:
        service.get_conversation(user.id, conversation.id)
    assert exc_info.value.code == "COPILOT_CONVERSATION_NOT_FOUND"


def test_copilot_action_is_confirmation_gated_and_single_use(db_session: Session) -> None:
    user, _, _, _, service = setup_copilot(db_session, propose_draft=True)
    conversation = service.create_conversation(user.id, "Draft help")
    _, _, action = service.send_message(
        user.id, conversation.id,
        SendCopilotMessageRequest(content="Create a draft about AI agents."),
    )

    assert action is not None
    assert action.status == "PENDING"
    assert db_session.scalar(select(func.count()).select_from(Post)) == 0

    completed = service.confirm_action(user.id, action.id)

    assert completed.status == "EXECUTED"
    assert db_session.scalar(select(func.count()).select_from(Post)) == 1
    created = db_session.scalar(select(Post))
    assert created is not None and created.status.value == "DRAFT"
    with pytest.raises(ApplicationError):
        service.confirm_action(user.id, action.id)
    assert db_session.scalar(select(func.count()).select_from(Post)) == 1


def test_copilot_action_cannot_cross_users(db_session: Session) -> None:
    user, _, _, _, service = setup_copilot(db_session, propose_draft=True)
    conversation = service.create_conversation(user.id, "Draft help")
    _, _, action = service.send_message(
        user.id, conversation.id,
        SendCopilotMessageRequest(content="Create a draft about AI agents."),
    )
    assert action is not None
    stranger = User(email="stranger@example.com", password_hash="hashed", display_name="Stranger")
    db_session.add(stranger)
    db_session.commit()

    with pytest.raises(ApplicationError):
        service.confirm_action(stranger.id, action.id)

    stored = db_session.get(AICopilotAction, action.id)
    assert stored is not None and stored.status == "PENDING"
    assert db_session.scalar(select(func.count()).select_from(Post)) == 0


def test_unknown_conversation_is_not_disclosed(db_session: Session) -> None:
    user, _, _, _, service = setup_copilot(db_session)
    with pytest.raises(ApplicationError) as exc_info:
        service.get_conversation(user.id, uuid4())
    assert exc_info.value.status_code == 404
