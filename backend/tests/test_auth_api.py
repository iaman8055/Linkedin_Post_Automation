from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


@pytest.mark.asyncio
async def test_authentication_api_flow(db_session: Session) -> None:
    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            registration = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "api@example.com",
                    "password": "strong-password-123",
                    "display_name": "API User",
                },
            )
            assert registration.status_code == 201
            auth = registration.json()
            assert auth["user"]["email"] == "api@example.com"
            assert auth["token_type"] == "bearer"

            profile = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {auth['access_token']}"},
            )
            assert profile.status_code == 200
            assert profile.json()["display_name"] == "API User"

            refreshed = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": auth["refresh_token"]},
            )
            assert refreshed.status_code == 200
            new_refresh_token = refreshed.json()["refresh_token"]

            logout = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": new_refresh_token},
            )
            assert logout.status_code == 204

            rejected = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": new_refresh_token},
            )
            assert rejected.status_code == 401
            assert rejected.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_authentication_errors_are_structured(db_session: Session) -> None:
    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "missing@example.com", "password": "wrong"},
            )
            assert response.status_code == 401
            assert response.json() == {
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                }
            }
    finally:
        app.dependency_overrides.clear()
