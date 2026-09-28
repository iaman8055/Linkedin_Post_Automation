from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.ai.router import get_provider_registry
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.post import Post
from app.models.user import User
from app.services.ai.contracts import AIGenerationRequest, AIGenerationResult
from app.services.ai.registry import AIProviderRegistry


class ApiGenerationProvider:
    name = "api-generation"

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult:
        if request.metadata.get("schema_name") == "linkedin_post_score":
            dimensions = [
                "hook", "clarity", "readability", "engagement_potential", "storytelling",
                "value", "cta", "structure", "authenticity",
            ]
            return AIGenerationResult(
                text="structured", provider=self.name, model=request.model,
                structured_output={
                    "overall_score": 82,
                    "breakdown": [
                        {"dimension": dimension, "score": 82, "explanation": "Clear assessment."}
                        for dimension in dimensions
                    ],
                },
            )
        if request.metadata.get("schema_name") == "linkedin_hooks":
            categories = ["curiosity", "contrarian", "story", "question", "lesson"]
            return AIGenerationResult(
                text="structured", provider=self.name, model=request.model,
                structured_output={"hooks": [
                    {"category": category, "text": f"Distinct {category} hook for AI agents"}
                    for category in categories
                ]},
            )
        if request.metadata.get("schema_name") == "assisted_post":
            return AIGenerationResult(
                text="structured",
                provider=self.name,
                model=request.model,
                structured_output={"content": "A clearer, stronger draft."},
            )
        return AIGenerationResult(
            text="structured",
            provider=self.name,
            model=request.model,
            structured_output={
                "posts": [
                    {
                        "title": "Generated title",
                        "angle": "Practical",
                        "content": "Generated API draft.",
                        "hashtags": ["AI"],
                    }
                ]
            },
        )


@pytest.mark.asyncio
async def test_ai_status_reports_missing_provider_without_faking_one(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="ai-status-secret-that-is-at-least-32-characters",
        ai_provider="not-installed",
        ai_model="configured-model",
    )
    user = User(email="ai-status@example.com", password_hash="hashed", display_name="AI User")
    db_session.add(user)
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/ai/status",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            assert response.json() == {
                "selected_provider": "not-installed",
                "selected_model": "configured-model",
                "provider_installed": False,
                "registered_providers": ["nvidia", "openai"],
            }
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_score_and_hooks_are_structured_and_advisory(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="ai-score-secret-that-is-at-least-32-characters",
        ai_provider="api-generation",
        ai_model="generation-model",
    )
    user = User(email="ai-score@example.com", password_hash="hashed", display_name="AI User")
    post = Post(user=user, content="A useful draft about AI agents.")
    db_session.add_all([user, post])
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)
    registry = AIProviderRegistry()
    registry.register(ApiGenerationProvider())

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_provider_registry] = lambda: registry
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            score = await client.post(f"/api/v1/ai/posts/{post.id}/score", headers=headers)
            assert score.status_code == 200
            assert score.json()["overall_score"] == 82
            assert len(score.json()["breakdown"]) == 9
            assert "does not predict virality" in score.json()["disclaimer"]

            hooks = await client.post(
                "/api/v1/ai/hooks/generate",
                headers=headers,
                json={"topic": "AI agents", "count": 5},
            )
            assert hooks.status_code == 200
            assert len(hooks.json()["hooks"]) == 5
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_assist_post_returns_reviewable_suggestion_without_overwriting(
    db_session: Session,
) -> None:
    settings = Settings(
        jwt_secret="ai-assist-secret-that-is-at-least-32-characters",
        ai_provider="api-generation",
        ai_model="generation-model",
    )
    user = User(email="ai-assist@example.com", password_hash="hashed", display_name="AI User")
    post = Post(user=user, content="Original draft")
    db_session.add_all([user, post])
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)
    registry = AIProviderRegistry()
    registry.register(ApiGenerationProvider())

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_provider_registry] = lambda: registry
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/ai/posts/{post.id}/assist",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"action": "improve"},
            )
            assert response.status_code == 200
            assert response.json()["content"] == "A clearer, stronger draft."
            db_session.refresh(post)
            assert post.content == "Original draft"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_posts_api_creates_reviewable_drafts(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="ai-api-secret-that-is-at-least-32-characters",
        ai_provider="api-generation",
        ai_model="generation-model",
    )
    user = User(email="ai-api@example.com", password_hash="hashed", display_name="AI User")
    db_session.add(user)
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)
    registry = AIProviderRegistry()
    registry.register(ApiGenerationProvider())

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_provider_registry] = lambda: registry
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ai/posts/generate",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "topic": "AI",
                    "subject": "AI agents",
                    "audience": "Software teams",
                    "number_of_posts": 1,
                },
            )
            assert response.status_code == 200
            assert response.json()["posts"][0]["status"] == "DRAFT"
            assert response.json()["posts"][0]["content"].endswith("#AI")
    finally:
        app.dependency_overrides.clear()
