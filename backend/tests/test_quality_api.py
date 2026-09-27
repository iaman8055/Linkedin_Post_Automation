from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.post import Post
from app.models.user import User


@pytest.mark.asyncio
async def test_quality_api_returns_structured_advisory_results(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="quality-api-secret-that-is-at-least-32-characters",
        ai_provider=None,
        ai_model=None,
    )
    user = User(email="quality-api@example.com", password_hash="hashed", display_name="Owner")
    post = Post(user=user, content="A short post.")
    db_session.add_all([user, post])
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/posts/{post.id}/quality-check",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "warning"
            assert body["issues"][0]["type"] == "length"
            assert body["ai_review_performed"] is False
    finally:
        app.dependency_overrides.clear()
