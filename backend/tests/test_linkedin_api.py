from collections.abc import Generator
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.api.linkedin.router import get_linkedin_client
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from tests.test_linkedin_service import FakeLinkedInClient


@pytest.mark.asyncio
async def test_linkedin_oauth_api_flow(db_session: Session) -> None:
    settings = Settings(
        jwt_secret="api-test-secret-that-is-at-least-32-characters",
        linkedin_client_id="linkedin-client-id",
        linkedin_client_secret="linkedin-client-secret",
        linkedin_token_encryption_key=Fernet.generate_key().decode(),
    )
    user = User(email="api-linkedin@example.com", password_hash="hashed", display_name="Member")
    db_session.add(user)
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_linkedin_client] = FakeLinkedInClient
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            connect = await client.get("/api/v1/linkedin/connect", headers=headers)
            assert connect.status_code == 200
            state = parse_qs(urlparse(connect.json()["authorization_url"]).query)["state"][0]

            callback = await client.get(
                "/api/v1/linkedin/callback",
                params={"code": "authorization-code", "state": state},
            )
            assert callback.status_code == 200
            account = callback.json()
            assert account["linkedin_member_id"] == "linkedin-member-123"

            status_response = await client.get("/api/v1/linkedin/status", headers=headers)
            assert status_response.status_code == 200
            assert len(status_response.json()["accounts"]) == 1

            published = await client.post(
                f"/api/v1/linkedin/{account['id']}/test-post",
                headers={**headers, "Idempotency-Key": "phase-five-test-0001"},
                json={"commentary": "A Phase 5 test post."},
            )
            assert published.status_code == 200
            assert published.json()["linkedin_post_id"] == "urn:li:share:123456"
            assert published.json()["status"] == "PUBLISHED"

            disconnected = await client.delete(
                f"/api/v1/linkedin/{account['id']}", headers=headers
            )
            assert disconnected.status_code == 204
    finally:
        app.dependency_overrides.clear()
