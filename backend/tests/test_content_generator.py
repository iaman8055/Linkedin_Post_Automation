from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import AIJobStatus, PostStatus
from app.models.user import User
from app.schemas.ai import GeneratePostsRequest
from app.services.ai.content_generator import ContentGenerator
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult, AIUsage
from app.services.ai.registry import AIProviderRegistry


class GeneratedPostsProvider:
    name = "generated-posts"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        assert request.response_schema is not None
        return AIGenerationResult(
            text="structured",
            provider=self.name,
            model=request.model,
            provider_request_id="generation-123",
            finish_reason="completed",
            usage=AIUsage(input_tokens=20, output_tokens=40, total_tokens=60),
            structured_output={
                "posts": [
                    {
                        "title": "Practical angle",
                        "angle": "A practical example",
                        "content": "First unique post.",
                        "hashtags": ["#AI", "LinkedIn"],
                    },
                    {
                        "title": "Contrarian angle",
                        "angle": "A misconception",
                        "content": "Second unique post.",
                        "hashtags": ["AI", "#Technology"],
                    },
                ]
            },
        )


def create_user(session: Session) -> UUID:
    user = User(
        email="generator@example.com", password_hash="hashed", display_name="Generator User"
    )
    session.add(user)
    session.commit()
    return user.id


def test_content_generator_saves_unique_drafts_and_safe_job_metadata(
    db_session: Session,
) -> None:
    registry = AIProviderRegistry()
    registry.register(GeneratedPostsProvider())
    settings = Settings(ai_provider="generated-posts", ai_model="generation-model")
    generator = ContentGenerator(db_session, settings, registry)
    user_id = create_user(db_session)

    job_id, posts = generator.generate_posts(
        user_id,
        GeneratePostsRequest(
            topic="Artificial intelligence",
            subject="AI agents",
            audience="Software leaders",
            number_of_posts=2,
            hashtag_count=2,
        ),
    )

    assert [post.status for post in posts] == [PostStatus.DRAFT, PostStatus.DRAFT]
    assert posts[0].content.endswith("#AI #LinkedIn")
    assert posts[0].content != posts[1].content
    job = generator.execution.jobs.get_for_user(job_id, user_id)
    assert job is not None
    assert job.status == AIJobStatus.SUCCEEDED
    assert "AI agents" not in str(job.input_data)
