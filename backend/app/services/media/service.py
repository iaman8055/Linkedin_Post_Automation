import re
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import MediaType, PostStatus
from app.models.post_media import PostMedia
from app.repositories.post_media import PostMediaRepository
from app.services.media.storage import MediaStorage
from app.services.posts import PostService

ALLOWED_MIME_TYPES = {
    "image/jpeg": MediaType.IMAGE,
    "image/png": MediaType.IMAGE,
    "image/gif": MediaType.IMAGE,
    "image/webp": MediaType.IMAGE,
    "video/mp4": MediaType.VIDEO,
    "application/pdf": MediaType.DOCUMENT,
}


class PostMediaService:
    def __init__(self, session: Session, settings: Settings, storage: MediaStorage) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage
        self.media = PostMediaRepository(session)

    def upload(
        self,
        user_id: UUID,
        post_id: UUID,
        *,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> PostMedia:
        post = PostService(self.session).get(user_id, post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError("POST_MEDIA_NOT_EDITABLE", "Only drafts accept media.", 409)
        if self.media.count_for_post(user_id, post_id) >= 10:
            raise ApplicationError("POST_MEDIA_LIMIT", "A post supports up to 10 attachments.", 422)
        media_type = ALLOWED_MIME_TYPES.get(content_type.lower())
        if media_type is None or not self._matches_signature(content_type.lower(), content):
            raise ApplicationError(
                "MEDIA_TYPE_INVALID",
                "The file type is not supported or does not match its content.",
                422,
            )
        limit = self._size_limit(media_type)
        if not content or len(content) > limit:
            raise ApplicationError(
                "MEDIA_SIZE_INVALID", f"The file must be between 1 byte and {limit} bytes.", 422
            )
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)[:180] or "upload"
        key = f"users/{user_id}/posts/{post_id}/{uuid4().hex}"
        self.storage.put(key, content)
        try:
            item = self.media.create_for_user(
                user_id,
                post_id=post_id,
                media_type=media_type,
                storage_key=key,
                public_url=None,
                mime_type=content_type.lower(),
                size_bytes=len(content),
                position=self.media.count_for_post(user_id, post_id),
                metadata_json={"filename": safe_name},
            )
            self.session.commit()
            self.session.refresh(item)
            return item
        except Exception:
            self.session.rollback()
            self.storage.delete(key)
            raise

    def list(self, user_id: UUID, post_id: UUID) -> list[PostMedia]:
        PostService(self.session).get(user_id, post_id)
        return self.media.list_for_post(user_id, post_id)

    def content(self, user_id: UUID, media_id: UUID) -> tuple[PostMedia, bytes]:
        item = self._get(user_id, media_id)
        return item, self.storage.read(item.storage_key)

    def delete(self, user_id: UUID, media_id: UUID) -> None:
        item = self._get(user_id, media_id)
        post = PostService(self.session).get(user_id, item.post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError(
                "POST_MEDIA_NOT_EDITABLE", "Only draft media can be removed.", 409
            )
        key = item.storage_key
        self.media.delete(item)
        self.session.commit()
        self.storage.delete(key)

    def _get(self, user_id: UUID, media_id: UUID) -> PostMedia:
        item = self.media.get_for_user(media_id, user_id)
        if item is None:
            raise ApplicationError("POST_MEDIA_NOT_FOUND", "Media attachment not found.", 404)
        return item

    def _size_limit(self, media_type: MediaType) -> int:
        if media_type is MediaType.IMAGE:
            return self.settings.storage_max_image_bytes
        if media_type is MediaType.VIDEO:
            return self.settings.storage_max_video_bytes
        return self.settings.storage_max_document_bytes

    @staticmethod
    def _matches_signature(content_type: str, content: bytes) -> bool:
        signatures = {
            "image/jpeg": content.startswith(b"\xff\xd8\xff"),
            "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/gif": content.startswith((b"GIF87a", b"GIF89a")),
            "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
            "video/mp4": len(content) >= 12 and content[4:8] == b"ftyp",
            "application/pdf": content.startswith(b"%PDF-"),
        }
        return signatures.get(content_type, False)
