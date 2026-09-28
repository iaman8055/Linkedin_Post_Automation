from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.post import Post
from app.models.user import User
from app.schemas.writing_profile import AnalyzeWritingStyleRequest
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.registry import AIProviderRegistry
from app.services.ai.writing_style_analyzer import WritingStyleAnalyzer


class StyleProvider:
    name = "style"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        assert request.metadata["schema_name"] == "writing_style_analysis"
        return AIGenerationResult(
            text="structured", provider=self.name, model=request.model,
            structured_output={
                "average_sentence_length": 13.5, "paragraph_length": "Short",
                "formality": "Conversational", "tone": "Direct and thoughtful",
                "emoji_frequency": "Low", "hashtag_frequency": "Medium",
                "storytelling": "Medium", "technical_depth": "Expert",
                "cta_style": "Ends with an open question",
                "opening_style": "Starts with a concise observation",
                "vocabulary_patterns": ["practical", "systems"],
            },
        )


def test_style_analysis_returns_editable_approximation(db_session: Session) -> None:
    user = User(email="style@example.com", password_hash="hashed", display_name="Writer")
    db_session.add(user)
    db_session.flush()
    db_session.add_all([
        Post(user_id=user.id, content="A concise first post.\n\nWhat do you think?"),
        Post(user_id=user.id, content="A second technical post with a practical lesson."),
    ])
    db_session.commit()
    registry = AIProviderRegistry()
    registry.register(StyleProvider())
    analyzer = WritingStyleAnalyzer(
        db_session, Settings(ai_provider="style", ai_model="test-model"), registry
    )

    result = analyzer.analyze(user.id, AnalyzeWritingStyleRequest())

    assert result.sample_size == 2
    assert "approximation" in result.disclaimer
    assert result.suggested_profile.technical_depth == "Expert"
    assert result.suggested_profile.additional_guidance["source"] == "ai_style_analysis"
