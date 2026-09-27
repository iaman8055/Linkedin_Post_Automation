from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User


@pytest.mark.asyncio
async def test_authenticated_post_editor_api(db_session: Session) -> None:
    settings = Settings(jwt_secret="post-api-secret-that-is-at-least-32-characters")
    user = User(
        email="post-api@example.com", password_hash="hashed", display_name="Post Author"
    )
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
                "/api/v1/posts",
                headers=headers,
                json={"title": "API draft", "content": "Draft content", "language": "English"},
            )
            assert created.status_code == 201
            post_id = created.json()["id"]
            assert created.json()["status"] == "DRAFT"

            listed = await client.get(
                "/api/v1/posts", headers=headers, params={"search": "Draft", "status": "DRAFT"}
            )
            assert listed.status_code == 200
            assert listed.json()["total"] == 1

            fetched = await client.get(f"/api/v1/posts/{post_id}", headers=headers)
            assert fetched.status_code == 200

            updated = await client.patch(
                f"/api/v1/posts/{post_id}", headers=headers, json={"content": "Updated content"}
            )
            assert updated.status_code == 200
            assert updated.json()["content"] == "Updated content"

            deleted = await client.delete(f"/api/v1/posts/{post_id}", headers=headers)
            assert deleted.status_code == 204

            missing = await client.get(f"/api/v1/posts/{post_id}", headers=headers)
            assert missing.status_code == 404

            invalid = await client.post(
                "/api/v1/posts", headers=headers, json={"content": "   ", "language": "English"}
            )
            assert invalid.status_code == 422
    finally:
        app.dependency_overrides.clear()
