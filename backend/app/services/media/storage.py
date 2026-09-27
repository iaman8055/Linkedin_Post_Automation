from pathlib import Path
from typing import Protocol

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]
from botocore.exceptions import BotoCoreError, ClientError  # type: ignore[import-untyped]

from app.core.config import Settings
from app.core.errors import ApplicationError


class MediaStorage(Protocol):
    def put(self, key: str, content: bytes) -> None: ...

    def read(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalMediaStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, content: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise ApplicationError("MEDIA_CONTENT_NOT_FOUND", "Media content was not found.", 404)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def _path(self, key: str) -> Path:
        candidate = (self.root / key).resolve()
        if self.root not in candidate.parents:
            raise ApplicationError(
                "MEDIA_STORAGE_KEY_INVALID", "Media storage key is invalid.", 500
            )
        return candidate


class S3MediaStorage:
    def __init__(
        self,
        *,
        bucket: str,
        region: str | None,
        endpoint: str | None,
        access_key: str | None,
        secret_key: str | None,
        force_path_style: bool = False,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if force_path_style else "auto"},
            ),
        )

    def put(self, key: str, content: bytes) -> None:
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        except (BotoCoreError, ClientError) as exc:
            raise ApplicationError(
                "MEDIA_STORAGE_WRITE_FAILED", "Media could not be stored.", 503
            ) from exc

    def read(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return bytes(response["Body"].read())
        except (BotoCoreError, ClientError) as exc:
            raise ApplicationError(
                "MEDIA_STORAGE_READ_FAILED", "Media content could not be retrieved.", 503
            ) from exc

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise ApplicationError(
                "MEDIA_STORAGE_DELETE_FAILED", "Media content could not be removed.", 503
            ) from exc


def create_media_storage(settings: Settings) -> MediaStorage:
    if settings.storage_provider == "local" and settings.app_env != "production":
        return LocalMediaStorage(settings.storage_local_path)
    if settings.storage_provider in {"s3", "supabase_s3"} and settings.storage_bucket:
        secret = (
            settings.storage_secret_key.get_secret_value()
            if settings.storage_secret_key is not None
            else None
        )
        return S3MediaStorage(
            bucket=settings.storage_bucket,
            region=settings.storage_region,
            endpoint=settings.storage_endpoint,
            access_key=settings.storage_access_key,
            secret_key=secret,
            force_path_style=(
                settings.storage_force_path_style
                or settings.storage_provider == "supabase_s3"
            ),
        )
    raise ApplicationError(
        "MEDIA_STORAGE_NOT_CONFIGURED",
        "A production object-storage adapter is not configured.",
        503,
    )
