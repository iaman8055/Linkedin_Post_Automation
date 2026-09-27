import hashlib
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus, PublishingStatus, ScheduleStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.publishing_log import PublishingLog
from app.models.schedule import Schedule
from app.repositories.linkedin_account import LinkedInAccountRepository
from app.repositories.publishing_log import PublishingLogRepository
from app.repositories.schedule import ScheduleRepository
from app.services.linkedin.client import LinkedInClient, LinkedInClientError
from app.services.linkedin.scopes import parse_linkedin_scopes
from app.services.linkedin.token_cipher import TokenCipher, TokenCipherError
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)


class ScheduledPostPublisher:
    required_scope = "w_member_social"

    def __init__(self, session: Session, settings: Settings, client: LinkedInClient) -> None:
        self.session = session
        self.settings = settings
        self.client = client
        self.schedules = ScheduleRepository(session)
        self.accounts = LinkedInAccountRepository(session)
        self.logs = PublishingLogRepository(session)

    def publish(self, schedule_id: UUID) -> Schedule:
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            raise ApplicationError("SCHEDULE_NOT_FOUND", "Schedule not found.", 404)
        post = schedule.post
        if schedule.status == ScheduleStatus.COMPLETED and post.status == PostStatus.PUBLISHED:
            return schedule
        if schedule.status != ScheduleStatus.ACTIVE or post.status != PostStatus.PUBLISHING:
            raise ApplicationError(
                "SCHEDULE_NOT_CLAIMED", "Schedule is not ready for publishing.", 409
            )

        stored_key = hashlib.sha256(
            f"scheduled:{schedule.id}:attempt:{schedule.attempt_count}".encode()
        ).hexdigest()
        existing = self.logs.get_by_idempotency_key(stored_key)
        if existing is not None:
            if existing.status == PublishingStatus.SUCCEEDED:
                self._complete(schedule, existing.external_post_id)
                return schedule
            raise ApplicationError(
                "LINKEDIN_PUBLISH_ALREADY_ATTEMPTED",
                "This scheduled post has already been attempted.",
                409,
            )

        publish_log = self.logs.add(
            PublishingLog(
                user_id=schedule.user_id,
                post=post,
                status=PublishingStatus.STARTED,
                attempt_number=schedule.attempt_count,
                idempotency_key=stored_key,
            )
        )
        self.session.commit()

        try:
            account = self._account(schedule.user_id)
            access_token = self._access_token(account)
            external_post_id = self.client.create_text_post(
                access_token=access_token,
                member_id=account.linkedin_member_id,
                commentary=post.content,
                api_version=self.settings.linkedin_api_version,
            )
        except ApplicationError as exc:
            self._fail(
                schedule,
                publish_log,
                exc.code,
                retry_safe=True,
                automatic_retry=False,
            )
            raise
        except LinkedInClientError as exc:
            code = (
                f"LINKEDIN_HTTP_{exc.status_code}"
                if exc.status_code
                else "LINKEDIN_NETWORK_ERROR"
            )
            retry_safe = exc.status_code is not None and exc.status_code < 500
            self._fail(
                schedule,
                publish_log,
                code,
                retry_safe=retry_safe,
                automatic_retry=exc.status_code == 429,
            )
            if exc.status_code == 401:
                account.is_connected = False
                self.session.commit()
            raise self._map_client_error(exc) from exc

        publish_log.status = PublishingStatus.SUCCEEDED
        publish_log.external_post_id = external_post_id
        NotificationService(self.session).create(
            schedule.user_id,
            event_type="POST_PUBLISHED",
            title="Post published",
            message="Your scheduled LinkedIn post was published successfully.",
            data={"post_id": str(post.id), "schedule_id": str(schedule.id)},
        )
        self._complete(schedule, external_post_id)
        logger.info(
            "scheduled_linkedin_post_published",
            extra={
                "user_id": str(schedule.user_id),
                "post_id": str(post.id),
                "schedule_id": str(schedule.id),
            },
        )
        return schedule

    def _account(self, user_id: UUID) -> LinkedInAccount:
        account = self.accounts.get_connected_for_user(user_id)
        if account is None or not account.encrypted_access_token:
            raise ApplicationError(
                "LINKEDIN_ACCOUNT_DISCONNECTED", "Reconnect the LinkedIn account.", 409
            )
        if account.token_expires_at is not None:
            expires_at = account.token_expires_at
            comparable = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
            if comparable <= datetime.now(UTC):
                raise ApplicationError(
                    "LINKEDIN_TOKEN_EXPIRED", "Reconnect the LinkedIn account.", 409
                )
        if self.required_scope not in parse_linkedin_scopes(account.scopes):
            raise ApplicationError(
                "LINKEDIN_SCOPE_MISSING",
                "Reconnect LinkedIn after enabling the Share on LinkedIn product.",
                403,
            )
        return account

    def _access_token(self, account: LinkedInAccount) -> str:
        encryption_key = self.settings.linkedin_token_encryption_key
        if encryption_key is None:
            raise ApplicationError("LINKEDIN_NOT_CONFIGURED", "LinkedIn is not configured.", 503)
        try:
            return TokenCipher(encryption_key.get_secret_value()).decrypt(
                account.encrypted_access_token
            )
        except TokenCipherError as exc:
            account.is_connected = False
            self.session.commit()
            raise ApplicationError(
                "LINKEDIN_TOKEN_UNAVAILABLE", "Reconnect the LinkedIn account.", 409
            ) from exc

    def _complete(self, schedule: Schedule, external_post_id: str | None) -> None:
        if not external_post_id:
            raise ApplicationError(
                "LINKEDIN_POST_ID_MISSING", "LinkedIn did not return a post identifier.", 502
            )
        schedule.post.status = PostStatus.PUBLISHED
        schedule.post.linkedin_post_id = external_post_id
        schedule.post.published_at = datetime.now(UTC)
        schedule.status = ScheduleStatus.COMPLETED
        schedule.next_run_at = None
        self.session.commit()

    def _fail(
        self,
        schedule: Schedule,
        log: PublishingLog,
        code: str,
        *,
        retry_safe: bool,
        automatic_retry: bool,
    ) -> None:
        will_retry = (
            retry_safe
            and automatic_retry
            and schedule.attempt_count < self.settings.publishing_max_attempts
        )
        if will_retry:
            delay = min(
                self.settings.publishing_retry_base_seconds
                * (2 ** max(schedule.attempt_count - 1, 0)),
                self.settings.publishing_retry_max_seconds,
            )
            schedule.post.status = PostStatus.SCHEDULED
            schedule.status = ScheduleStatus.ACTIVE
            schedule.next_run_at = datetime.now(UTC) + timedelta(seconds=delay)
        else:
            schedule.post.status = PostStatus.FAILED
            schedule.status = ScheduleStatus.COMPLETED
            schedule.next_run_at = None
        log.status = PublishingStatus.FAILED
        log.error_code = code
        log.error_message = "LinkedIn post creation failed."
        log.response_metadata = {
            "retry_safe": retry_safe,
            "automatic_retry_scheduled": will_retry,
            "outcome_uncertain": not retry_safe,
        }
        NotificationService(self.session).create(
            schedule.user_id,
            event_type="POST_RETRY_SCHEDULED" if will_retry else "POST_FAILED",
            title="Publishing retry scheduled" if will_retry else "Post publishing failed",
            message=(
                "LinkedIn temporarily rejected the post; another attempt is scheduled."
                if will_retry else "The scheduled LinkedIn post could not be published."
            ),
            data={"post_id": str(schedule.post_id), "schedule_id": str(schedule.id), "code": code},
        )
        self.session.commit()
        logger.warning(
            "scheduled_linkedin_post_failed",
            extra={"schedule_id": str(schedule.id), "post_id": str(schedule.post_id), "code": code},
        )

    @staticmethod
    def _map_client_error(error: LinkedInClientError) -> ApplicationError:
        if error.status_code == 401:
            return ApplicationError("LINKEDIN_TOKEN_INVALID", "Reconnect LinkedIn.", 409)
        if error.status_code == 403:
            return ApplicationError(
                "LINKEDIN_PUBLISH_PERMISSION_DENIED", "LinkedIn denied publishing.", 403
            )
        if error.status_code == 429:
            return ApplicationError("LINKEDIN_RATE_LIMITED", "LinkedIn rate limit reached.", 429)
        return ApplicationError(
            "LINKEDIN_PUBLISH_FAILED", "Unable to publish the LinkedIn post.", 502
        )
