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
async def test_writing_profile_api_flow(db_session: Session) -> None:
    settings = Settings(jwt_secret="writing-profile-secret-that-is-at-least-32-characters")
    user = User(email="profile-api@example.com", password_hash="hashed", display_name="Owner")
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
                "/api/v1/writing-profiles",
                headers=headers,
                json={"name": "My voice", "tone": "Warm", "preferred_vocabulary": ["clear"]},
            )
            assert created.status_code == 201
            assert created.json()["is_default"] is True
            profile_id = created.json()["id"]

            listed = await client.get("/api/v1/writing-profiles", headers=headers)
            assert listed.status_code == 200
            assert listed.json()["total"] == 1

            updated = await client.patch(
                f"/api/v1/writing-profiles/{profile_id}",
                headers=headers,
                json={"technical_depth": "Expert"},
            )
            assert updated.status_code == 200
            assert updated.json()["technical_depth"] == "Expert"
    finally:
        app.dependency_overrides.clear()
