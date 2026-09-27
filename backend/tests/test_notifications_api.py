from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.services.notifications import NotificationService


@pytest.mark.asyncio
async def test_notifications_are_owned_and_can_be_marked_read(db_session: Session) -> None:
    settings = Settings(jwt_secret="notifications-secret-that-is-at-least-32-characters")
    owner = User(email="notifications@example.com", password_hash="hashed", display_name="Owner")
    other = User(
        email="other-notifications@example.com", password_hash="hashed", display_name="Other"
    )
    db_session.add_all([owner, other])
    db_session.flush()
    owned = NotificationService(db_session).create(
        owner.id, event_type="POST_PUBLISHED", title="Published", message="Post published."
    )
    NotificationService(db_session).create(
        other.id, event_type="POST_FAILED", title="Private", message="Other user's event."
    )
    db_session.commit()
    access_token, _ = create_access_token(owner.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            listed = await client.get("/api/v1/notifications", headers=headers)
            assert listed.status_code == 200
            assert listed.json()["unread_count"] == 1
            assert [item["title"] for item in listed.json()["items"]] == ["Published"]

            read = await client.patch(
                f"/api/v1/notifications/{owned.id}/read", headers=headers
            )
            assert read.status_code == 200
            assert read.json()["read_at"] is not None
            count = await client.get("/api/v1/notifications/unread-count", headers=headers)
            assert count.json() == {"unread_count": 0}
    finally:
        app.dependency_overrides.clear()
