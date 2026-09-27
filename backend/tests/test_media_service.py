from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.post import Post
from app.models.user import User
from app.services.media.service import PostMediaService
from app.services.media.storage import LocalMediaStorage, S3MediaStorage


def setup_post(session: Session) -> tuple[User, Post]:
    user = User(email="media@example.com", password_hash="hashed", display_name="Media")
    post = Post(user=user, content="Draft with media")
    session.add_all([user, post])
    session.commit()
    return user, post


def test_media_upload_stores_binary_outside_database(
    db_session: Session, tmp_path: Path
) -> None:
    user, post = setup_post(db_session)
    storage = LocalMediaStorage(str(tmp_path))
    service = PostMediaService(db_session, Settings(), storage)
    content = b"\x89PNG\r\n\x1a\n" + b"image-data"

    item = service.upload(
        user.id,
        post.id,
        filename="diagram.png",
        content_type="image/png",
        content=content,
    )

    assert item.metadata_json == {"filename": "diagram.png"}
    assert item.size_bytes == len(content)
    assert storage.read(item.storage_key) == content
    assert not hasattr(item, "content")
    service.delete(user.id, item.id)
    with pytest.raises(ApplicationError) as missing:
        storage.read(item.storage_key)
    assert missing.value.code == "MEDIA_CONTENT_NOT_FOUND"


def test_media_rejects_spoofed_mime_type(db_session: Session, tmp_path: Path) -> None:
    user, post = setup_post(db_session)
    service = PostMediaService(db_session, Settings(), LocalMediaStorage(str(tmp_path)))
    with pytest.raises(ApplicationError) as invalid:
        service.upload(
            user.id,
            post.id,
            filename="not-an-image.png",
            content_type="image/png",
            content=b"plain text",
        )
    assert invalid.value.code == "MEDIA_TYPE_INVALID"


def test_s3_storage_uses_private_object_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    objects: dict[str, bytes] = {}
    client_options: dict[str, object] = {}

    class Body:
        def __init__(self, value: bytes) -> None:
            self.value = value

        def read(self) -> bytes:
            return self.value

    class Client:
        def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
            objects[f"{Bucket}/{Key}"] = Body

        def get_object(self, *, Bucket: str, Key: str) -> dict[str, Body]:
            return {"Body": Body(objects[f"{Bucket}/{Key}"])}

        def delete_object(self, *, Bucket: str, Key: str) -> None:
            objects.pop(f"{Bucket}/{Key}")

    def create_client(*args: object, **kwargs: object) -> Client:
        client_options.update(kwargs)
        return Client()

    monkeypatch.setattr("app.services.media.storage.boto3.client", create_client)
    storage = S3MediaStorage(
        bucket="private-media",
        region=None,
        endpoint=None,
        access_key=None,
        secret_key=None,
        force_path_style=True,
    )
    storage.put("users/one/file", b"content")
    assert storage.read("users/one/file") == b"content"
    storage.delete("users/one/file")
    assert objects == {}
    config = cast(Any, client_options["config"])
    assert config.s3 == {"addressing_style": "path"}
    assert config.signature_version == "s3v4"
