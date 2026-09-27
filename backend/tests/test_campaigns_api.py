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
async def test_campaign_api_lifecycle_and_post_membership(db_session: Session) -> None:
    settings = Settings(jwt_secret="campaign-api-secret-that-is-at-least-32-characters")
    user = User(email="campaign-api@example.com", password_hash="hashed", display_name="Owner")
    post = Post(user=user, content="Campaign draft")
    db_session.add(user)
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post(
                "/api/v1/campaigns",
                headers=headers,
                json={"name": "AI Week", "topic": "AI", "timezone": "UTC"},
            )
            assert created.status_code == 201
            campaign_id = created.json()["id"]
            assert created.json()["approval_mode"] == "MANUAL"

            attached = await client.post(
                f"/api/v1/campaigns/{campaign_id}/posts/{post.id}", headers=headers
            )
            assert attached.status_code == 200
            assert attached.json()["post_count"] == 1

            posts = await client.get(
                f"/api/v1/campaigns/{campaign_id}/posts", headers=headers
            )
            assert posts.status_code == 200
            assert posts.json()["items"][0]["campaign_id"] == campaign_id

            active = await client.post(
                f"/api/v1/campaigns/{campaign_id}/transition",
                headers=headers,
                json={"status": "ACTIVE"},
            )
            assert active.status_code == 200
            assert active.json()["status"] == "ACTIVE"

            invalid_delete = await client.delete(
                f"/api/v1/campaigns/{campaign_id}", headers=headers
            )
            assert invalid_delete.status_code == 409
    finally:
        app.dependency_overrides.clear()
