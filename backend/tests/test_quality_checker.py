from hashlib import sha256

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.post import Post
from app.models.user import User
from app.schemas.quality import QualityStatus
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.quality_checker import QualityChecker
from app.services.ai.registry import AIProviderRegistry


class QualityProvider:
    name = "quality-provider"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        assert request.response_schema is not None
        assert "Do not rewrite" in request.messages[0].content
        return AIGenerationResult(
            text="structured",
            provider=self.name,
            model=request.model,
            structured_output={"issues": [{
                "type": "unsupported_claim",
                "severity": "medium",
                "message": "A numerical claim has no supporting context.",
                "suggestion": "Add a source or qualify the claim.",
            }]},
        )


def make_posts(session: Session) -> tuple[User, Post, Post]:
    user = User(email="quality@example.com", password_hash="hashed", display_name="Quality")
    content = "AI improves every workflow by 90%. #AI #Tech #Work #Future #Agents #Automation"
    fingerprint = sha256(content.encode("utf-8")).hexdigest()
    first = Post(user=user, title="One", content=content, content_fingerprint=fingerprint)
    second = Post(user=user, title="Two", content=content, content_fingerprint=fingerprint)
    session.add_all([user, first, second])
    session.commit()
    return user, first, second


def test_deterministic_quality_checks_work_without_ai(db_session: Session) -> None:
    user, first, _ = make_posts(db_session)
    result = QualityChecker(db_session, Settings(), AIProviderRegistry()).check(user.id, first.id)
    types = {issue.type for issue in result.issues}
    assert {"excessive_hashtags", "length", "duplicate_content"} <= types
    assert result.status is QualityStatus.FAIL
    assert result.ai_review_performed is False


def test_ai_quality_issues_are_structured_and_non_destructive(db_session: Session) -> None:
    user, first, _ = make_posts(db_session)
    registry = AIProviderRegistry()
    registry.register(QualityProvider())
    settings = Settings(ai_provider="quality-provider", ai_model="quality-model")
    original = first.content
    result = QualityChecker(db_session, settings, registry).check(user.id, first.id)
    assert result.ai_review_performed is True
    assert result.job_id is not None
    assert any(issue.type == "unsupported_claim" for issue in result.issues)
    assert first.content == original
