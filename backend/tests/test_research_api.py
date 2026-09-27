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
async def test_research_status_and_empty_source_library(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="research-api-secret-that-is-at-least-32-characters",
        research_provider=None,
        research_api_key=None,
    )
    user = User(email="research-api@example.com", password_hash="hashed", display_name="Owner")
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
            status = await client.get("/api/v1/research/status", headers=headers)
            assert status.status_code == 200
            assert status.json() == {"selected_provider": None, "configured": False}
            sources = await client.get("/api/v1/research/sources", headers=headers)
            assert sources.status_code == 200
            assert sources.json()["total"] == 0
            unavailable = await client.post(
                "/api/v1/research/search", headers=headers, json={"query": "AI agents"}
            )
            assert unavailable.status_code == 503
    finally:
        app.dependency_overrides.clear()
