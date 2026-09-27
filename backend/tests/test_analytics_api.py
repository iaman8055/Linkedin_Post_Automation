from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.linkedin_account import LinkedInAccount
from app.models.user import User


@pytest.mark.asyncio
async def test_analytics_status_reports_restricted_permission(db_session: Session) -> None:
    settings = Settings(jwt_secret="analytics-api-secret-that-is-at-least-32-characters")
    user = User(email="analytics-api@example.com", password_hash="hashed", display_name="Owner")
    account = LinkedInAccount(
        user=user,
        linkedin_member_id="member-1",
        encrypted_access_token="encrypted",
        scopes="openid w_member_social",
        is_connected=True,
    )
    db_session.add_all([user, account])
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/status",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert response.status_code == 200
            assert response.json() == {
                "connected": True,
                "permission_granted": False,
                "required_scope": "r_member_postAnalytics",
                "collection_available": False,
            }
            overview = await client.get(
                "/api/v1/analytics/overview",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert overview.status_code == 200
            assert overview.json()["total_impressions"] is None
            insights = await client.get(
                "/api/v1/analytics/insights",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert insights.status_code == 200
            assert insights.json()["status"] == "insufficient_data"
            assert insights.json()["minimum_required"] == 5
    finally:
        app.dependency_overrides.clear()
