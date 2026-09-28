from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import PostStatus
from app.models.post import Post
from app.models.user import User
from app.schemas.engagement import CreateExperimentRequest, GenerateCommentResponsesRequest
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.registry import AIProviderRegistry
from app.services.engagement import EngagementService


class EngagementProvider:
    name = "engagement"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        if request.metadata["schema_name"] == "comment_responses":
            output = {"suggestions": [
                {"style": style, "response": f"Editable {style} response"}
                for style in ["professional", "friendly", "concise", "thoughtful", "humorous"]
            ]}
        else:
            output = {"versions": [
                {
                    "label": "A", "title": "Version A", "content": "A distinct opening.\n\nBody.",
                    "change_summary": "Uses a question hook.",
                },
                {
                    "label": "B", "title": "Version B", "content": "A bold opening.\n\nBody.",
                    "change_summary": "Uses a bold hook.",
                },
            ]}
        return AIGenerationResult(
            text="structured", provider=self.name, model=request.model, structured_output=output
        )


def setup(db_session: Session) -> tuple[EngagementService, User, Post]:
    user = User(email="engagement@example.com", password_hash="hashed", display_name="Owner")
    post = Post(user=user, title="Source", content="Original source post.")
    db_session.add_all([user, post])
    db_session.commit()
    registry = AIProviderRegistry()
    registry.register(EngagementProvider())
    service = EngagementService(
        db_session,
        Settings(ai_provider="engagement", ai_model="test-model"),
        registry,
    )
    return service, user, post


def test_comment_suggestions_are_review_only_and_cover_each_style(db_session: Session) -> None:
    service, user, _ = setup(db_session)
    _, result = service.comment_responses(
        user.id, GenerateCommentResponsesRequest(comment="I had a different experience.")
    )
    assert {item.style for item in result.suggestions} == {
        "professional", "friendly", "concise", "thoughtful", "humorous"
    }
    assert "Review and edit" in service.comment_disclaimer


def test_experiment_creates_drafts_and_waits_for_real_publication(db_session: Session) -> None:
    service, user, source = setup(db_session)
    _, experiment = service.create_experiment(user.id, CreateExperimentRequest(
        source_post_id=source.id, name="Hook experiment", comparison_axis="hook"
    ))
    comparison = service.compare(user.id, experiment.id)
    assert experiment.version_a.status is PostStatus.DRAFT
    assert experiment.version_b.status is PostStatus.DRAFT
    assert comparison.status == "awaiting_publication"
    assert comparison.better_version is None
