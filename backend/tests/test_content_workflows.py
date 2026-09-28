from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import ContentPlanStatus, IdeaStatus, PostStatus
from app.models.user import User
from app.schemas.content_workflows import (
    ContentIdeaCreate,
    GenerateContentPlanRequest,
    GenerateIdeasRequest,
    RepurposeRequest,
)
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.registry import AIProviderRegistry
from app.services.content_workflows import ContentWorkflowService


class WorkflowProvider:
    name = "workflow"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        schema = request.metadata["schema_name"]
        if schema == "content_ideas":
            output = {"ideas": [self._idea(index) for index in range(3)]}
        elif schema == "repurposed_content":
            output = {"items": [
                {
                    "title": f"Series {index}",
                    "content": f"Useful draft {index}",
                    "angle": "Practical",
                }
                for index in range(2)
            ]}
        else:
            output = {"items": [
                {
                    "topic": "AI", "post_type": "Educational",
                    "title": f"Plan item {index}", "content": f"Complete planned draft {index}.",
                }
                for index in range(3)
            ]}
        return AIGenerationResult(
            text="structured", provider=self.name, model=request.model, structured_output=output
        )

    @staticmethod
    def _idea(index: int) -> dict[str, str]:
        return {
            "title": f"Idea {index}", "topic": "AI", "category": "educational",
            "angle": f"Angle {index}", "description": "A practical content direction.",
            "suggested_hook": f"A useful opening hook {index}", "suggested_format": "Short post",
        }


def service(db_session: Session) -> tuple[ContentWorkflowService, User]:
    user = User(email="studio@example.com", password_hash="hashed", display_name="Studio User")
    db_session.add(user)
    db_session.commit()
    registry = AIProviderRegistry()
    registry.register(WorkflowProvider())
    settings = Settings(
        jwt_secret="workflow-secret-that-is-at-least-32-characters",
        ai_provider="workflow", ai_model="test-model",
    )
    return ContentWorkflowService(db_session, settings, registry), user


def test_ideas_can_be_generated_saved_and_converted_to_draft(db_session: Session) -> None:
    workflows, user = service(db_session)
    _, generated = workflows.generate_ideas(
        user.id, GenerateIdeasRequest(topics=["AI"], count=3)
    )
    idea = workflows.save_idea(user.id, ContentIdeaCreate(**generated.ideas[0].model_dump()))
    post = workflows.create_post_from_idea(user.id, idea.id)

    assert len(generated.ideas) == 3
    assert idea.status is IdeaStatus.USED
    assert post.status is PostStatus.DRAFT
    assert generated.ideas[0].suggested_hook in post.content


def test_repurposing_creates_reviewable_drafts(db_session: Session) -> None:
    workflows, user = service(db_session)
    _, posts = workflows.repurpose(user.id, RepurposeRequest(
        source_type="paste_text",
        source_content="A long source with enough useful details to reuse.",
        output_format="linkedin_post", count=2,
    ))
    assert [post.status for post in posts] == [PostStatus.DRAFT, PostStatus.DRAFT]


def test_plan_approval_defaults_to_drafts_without_schedules(db_session: Session) -> None:
    workflows, user = service(db_session)
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
    _, plan = workflows.generate_plan(user.id, GenerateContentPlanRequest(
        name="AI week", frequency="3_per_week", duration_days=7, topics=["AI"],
        audience="Developers", start_date=next_monday, posting_time=time(10), timezone="UTC",
    ))
    result = workflows.approve_plan(user.id, plan.id, schedule_for_auto_publish=False)
    assert result.plan.status is ContentPlanStatus.APPROVED
    assert result.scheduled_count == 0
    assert len(result.created_post_ids) == 3
    assert all(item.post_id is not None for item in result.plan.items)
