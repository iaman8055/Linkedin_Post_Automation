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
async def test_template_api_flow(db_session: Session) -> None:
    settings = Settings(jwt_secret="template-api-secret-that-is-at-least-32-characters")
    user = User(email="template-api@example.com", password_hash="hashed", display_name="Owner")
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
                "/api/v1/templates",
                headers=headers,
                json={"name": "API template", "body": "Hello {{audience}}"},
            )
            assert created.status_code == 201
            template_id = created.json()["id"]
            assert created.json()["placeholders"] == ["audience"]

            listed = await client.get(
                "/api/v1/templates", headers=headers, params={"search": "API"}
            )
            assert listed.status_code == 200
            assert listed.json()["total"] == 1

            rendered = await client.post(
                f"/api/v1/templates/{template_id}/render",
                headers=headers,
                json={"values": {"audience": "engineering leaders"}},
            )
            assert rendered.status_code == 200
            assert rendered.json()["content"] == "Hello engineering leaders"

            archived = await client.post(
                f"/api/v1/templates/{template_id}/archive", headers=headers
            )
            assert archived.status_code == 200
            assert archived.json()["status"] == "ARCHIVED"
    finally:
        app.dependency_overrides.clear()
