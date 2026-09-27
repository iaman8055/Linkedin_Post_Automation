import hashlib
import logging
from datetime import UTC, datetime
from urllib.parse import unquote_plus
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus, PublishingStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.post import Post
from app.models.publishing_log import PublishingLog
from app.repositories.linkedin_account import LinkedInAccountRepository
from app.repositories.post import PostRepository
from app.repositories.publishing_log import PublishingLogRepository
from app.services.linkedin.client import LinkedInClient, LinkedInClientError
from app.services.linkedin.token_cipher import TokenCipher, TokenCipherError

logger = logging.getLogger(__name__)


class TestPostPublisher:
    required_scope = "w_member_social"

    def __init__(self, session: Session, settings: Settings, client: LinkedInClient) -> None:
        self.session = session
        self.settings = settings
        self.client = client
        self.accounts = LinkedInAccountRepository(session)
        self.posts = PostRepository(session)
        self.logs = PublishingLogRepository(session)

    def publish(
        self,
        *,
        user_id: UUID,
        account_id: UUID,
        commentary: str,
        idempotency_key: str,
    ) -> Post:
        account = self.accounts.get_for_user(account_id, user_id)
        if account is None:
            raise ApplicationError("LINKEDIN_ACCOUNT_NOT_FOUND", "LinkedIn account not found.", 404)
        if not account.is_connected or not account.encrypted_access_token:
            raise ApplicationError(
                "LINKEDIN_ACCOUNT_DISCONNECTED", "Reconnect the LinkedIn account.", 409
            )
        if account.token_expires_at is not None and self._is_expired(account.token_expires_at):
            raise ApplicationError(
                "LINKEDIN_TOKEN_EXPIRED", "Reconnect the LinkedIn account.", 409
            )
        if self.required_scope not in self._parse_scopes(account.scopes):
            raise ApplicationError(
                "LINKEDIN_SCOPE_MISSING",
                "Reconnect LinkedIn after enabling the Share on LinkedIn product.",
                403,
            )

        stored_key = hashlib.sha256(f"{user_id}:{idempotency_key}".encode()).hexdigest()
        existing = self.logs.get_by_idempotency_key(stored_key)
        if existing is not None:
            if existing.status is PublishingStatus.SUCCEEDED:
                return existing.post
            raise ApplicationError(
                "LINKEDIN_PUBLISH_ALREADY_ATTEMPTED",
                "This publish request has already been attempted.",
                409,
            )

        encryption_key = self.settings.linkedin_token_encryption_key
        if encryption_key is None:
            raise ApplicationError("LINKEDIN_NOT_CONFIGURED", "LinkedIn is not configured.", 503)
        try:
            access_token = TokenCipher(encryption_key.get_secret_value()).decrypt(
                account.encrypted_access_token
            )
        except TokenCipherError as exc:
            account.is_connected = False
            self.session.commit()
            raise ApplicationError(
                "LINKEDIN_TOKEN_UNAVAILABLE", "Reconnect the LinkedIn account.", 409
            ) from exc

        post = self.posts.create_for_user(
            user_id,
            content=commentary,
            status=PostStatus.PUBLISHING,
        )
        publish_log = self.logs.add(
            PublishingLog(
                user_id=user_id,
                post=post,
                status=PublishingStatus.STARTED,
                attempt_number=1,
                idempotency_key=stored_key,
            )
        )
        self.session.commit()

        try:
            external_post_id = self.client.create_text_post(
                access_token=access_token,
                member_id=account.linkedin_member_id,
                commentary=commentary,
                api_version=self.settings.linkedin_api_version,
            )
        except LinkedInClientError as exc:
            self._record_failure(account, post, publish_log, exc)
            raise self._map_publish_error(exc) from exc

        now = datetime.now(UTC)
        post.status = PostStatus.PUBLISHED
        post.linkedin_post_id = external_post_id
        post.published_at = now
        publish_log.status = PublishingStatus.SUCCEEDED
        publish_log.external_post_id = external_post_id
        self.session.commit()
        logger.info(
            "linkedin_test_post_published",
            extra={"user_id": str(user_id), "post_id": str(post.id)},
        )
        return post

    def _record_failure(
        self,
        account: LinkedInAccount,
        post: Post,
        publish_log: PublishingLog,
        error: LinkedInClientError,
    ) -> None:
        post.status = PostStatus.FAILED
        publish_log.status = PublishingStatus.FAILED
        publish_log.error_code = (
            f"LINKEDIN_HTTP_{error.status_code}" if error.status_code else "LINKEDIN_NETWORK_ERROR"
        )
        publish_log.error_message = "LinkedIn post creation failed."
        if error.status_code == 401:
            account.is_connected = False
            logger.warning("linkedin_token_rejected", extra={"user_id": str(post.user_id)})
        self.session.commit()

    @staticmethod
    def _map_publish_error(error: LinkedInClientError) -> ApplicationError:
        if error.status_code == 401:
            return ApplicationError(
                "LINKEDIN_TOKEN_INVALID", "Reconnect the LinkedIn account.", 409
            )
        if error.status_code == 403:
            return ApplicationError(
                "LINKEDIN_PUBLISH_PERMISSION_DENIED",
                "LinkedIn did not permit publishing for this account.",
                403,
            )
        if error.status_code == 429:
            return ApplicationError(
                "LINKEDIN_RATE_LIMITED", "LinkedIn rate limit reached. Try again later.", 429
            )
        return ApplicationError(
            "LINKEDIN_PUBLISH_FAILED", "Unable to publish the LinkedIn post.", 502
        )

    @staticmethod
    def _parse_scopes(value: str) -> set[str]:
        return set(unquote_plus(value).split())

    @staticmethod
    def _is_expired(value: datetime) -> bool:
        comparable = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return comparable <= datetime.now(UTC)
