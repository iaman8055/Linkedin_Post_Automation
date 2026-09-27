from collections.abc import Generator
from pathlib import Path

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
async def test_media_api_upload_list_content_and_delete(
    db_session: Session, tmp_path: Path
) -> None:
    settings = Settings(
        jwt_secret="media-api-secret-that-is-at-least-32-characters",
        storage_provider="local",
        storage_local_path=str(tmp_path),
    )
    user = User(email="media-api@example.com", password_hash="hashed", display_name="Owner")
    post = Post(user=user, content="Media draft")
    db_session.add_all([user, post])
    db_session.commit()
    access_token, _ = create_access_token(user.id, settings)

    def override_database() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[get_settings] = lambda: settings
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/pdf"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            uploaded = await client.post(
                f"/api/v1/posts/{post.id}/media",
                params={"filename": "report.pdf"},
                headers=headers,
                content=b"%PDF-1.7\ncontent",
            )
            assert uploaded.status_code == 201
            media_id = uploaded.json()["id"]
            assert uploaded.json()["media_type"] == "DOCUMENT"

            listed = await client.get(
                f"/api/v1/posts/{post.id}/media",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert listed.status_code == 200
            assert listed.json()["items"][0]["metadata_json"]["filename"] == "report.pdf"

            content = await client.get(
                f"/api/v1/media/{media_id}/content",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert content.content.startswith(b"%PDF-")
            deleted = await client.delete(
                f"/api/v1/media/{media_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert deleted.status_code == 204
    finally:
        app.dependency_overrides.clear()
