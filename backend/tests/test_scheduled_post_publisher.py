from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus, PublishingStatus, ScheduleStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.post import Post
from app.models.publishing_log import PublishingLog
from app.models.schedule import Schedule
from app.models.user import User
from app.services.linkedin.client import LinkedInClientError
from app.services.linkedin.token_cipher import TokenCipher
from app.services.publishing.scheduled_post import ScheduledPostPublisher
from app.services.scheduling import SchedulingService
from tests.test_linkedin_service import FakeLinkedInClient


class FailingClient(FakeLinkedInClient):
    def __init__(self, status_code: int | None) -> None:
        super().__init__()
        self.status_code = status_code

    def create_text_post(
        self,
        *,
        access_token: str,
        member_id: str,
        commentary: str,
        api_version: str,
    ) -> str:
        self.publish_calls += 1
        raise LinkedInClientError("publish failed", self.status_code)


def settings() -> Settings:
    return Settings(
        jwt_secret="scheduled-publisher-secret-at-least-32-characters",
        linkedin_client_id="client-id",
        linkedin_client_secret="client-secret",
        linkedin_token_encryption_key=Fernet.generate_key().decode(),
    )


def claimed_schedule(
    session: Session, configured: Settings, *, with_account: bool = True
) -> tuple[Schedule, FakeLinkedInClient]:
    user = User(email="scheduled@example.com", password_hash="hashed", display_name="Scheduler")
    post = Post(user=user, content="A scheduled LinkedIn post.", status=PostStatus.PUBLISHING)
    schedule = Schedule(
        user=user,
        post=post,
        status=ScheduleStatus.ACTIVE,
        scheduled_for=datetime.now(UTC) - timedelta(minutes=1),
        next_run_at=datetime.now(UTC) - timedelta(minutes=1),
        attempt_count=1,
    )
    session.add_all([user, post, schedule])
    if with_account:
        encryption_key = configured.linkedin_token_encryption_key
        assert encryption_key is not None
        session.add(
            LinkedInAccount(
                user=user,
                linkedin_member_id="linkedin-member-123",
                encrypted_access_token=TokenCipher(
                    encryption_key.get_secret_value()
                ).encrypt("real-access-token"),
                scopes="openid profile email w_member_social",
            )
        )
    session.commit()
    return schedule, FakeLinkedInClient()


def test_claimed_schedule_is_published_once(db_session: Session) -> None:
    configured = settings()
    schedule, client = claimed_schedule(db_session, configured)
    publisher = ScheduledPostPublisher(db_session, configured, client)

    published = publisher.publish(schedule.id)
    repeated = publisher.publish(schedule.id)

    assert repeated.id == published.id
    assert client.publish_calls == 1
    assert published.status is ScheduleStatus.COMPLETED
    assert published.next_run_at is None
    assert published.post.status is PostStatus.PUBLISHED
    assert published.post.linkedin_post_id == "urn:li:share:123456"
    log = db_session.query(PublishingLog).one()
    assert log.status is PublishingStatus.SUCCEEDED
    assert log.attempt_number == 1


def test_missing_linkedin_account_records_failure(db_session: Session) -> None:
    configured = settings()
    schedule, client = claimed_schedule(db_session, configured, with_account=False)

    with pytest.raises(ApplicationError) as error:
        ScheduledPostPublisher(db_session, configured, client).publish(schedule.id)

    assert error.value.code == "LINKEDIN_ACCOUNT_DISCONNECTED"
    assert schedule.status is ScheduleStatus.COMPLETED
    assert schedule.post.status is PostStatus.FAILED
    log = db_session.query(PublishingLog).one()
    assert log.status is PublishingStatus.FAILED
    assert log.error_code == "LINKEDIN_ACCOUNT_DISCONNECTED"

    retried = SchedulingService(db_session, configured).retry_failed(
        schedule.user_id, schedule.id
    )
    assert retried.status is ScheduleStatus.ACTIVE
    assert retried.post.status is PostStatus.SCHEDULED


def test_rate_limit_uses_exponential_safe_retry(db_session: Session) -> None:
    configured = settings()
    schedule, _ = claimed_schedule(db_session, configured)

    with pytest.raises(ApplicationError) as error:
        ScheduledPostPublisher(db_session, configured, FailingClient(429)).publish(schedule.id)

    assert error.value.code == "LINKEDIN_RATE_LIMITED"
    assert schedule.status is ScheduleStatus.ACTIVE
    assert schedule.post.status is PostStatus.SCHEDULED
    assert schedule.next_run_at is not None
    first_log = db_session.query(PublishingLog).one()
    assert first_log.response_metadata == {
        "retry_safe": True,
        "automatic_retry_scheduled": True,
        "outcome_uncertain": False,
    }

    schedule.attempt_count = 2
    schedule.post.status = PostStatus.PUBLISHING
    db_session.commit()
    successful_client = FakeLinkedInClient()
    ScheduledPostPublisher(db_session, configured, successful_client).publish(schedule.id)
    assert successful_client.publish_calls == 1
    assert db_session.query(PublishingLog).count() == 2
    assert schedule.post.status is PostStatus.PUBLISHED


def test_uncertain_network_failure_cannot_be_retried(db_session: Session) -> None:
    configured = settings()
    schedule, _ = claimed_schedule(db_session, configured)

    with pytest.raises(ApplicationError):
        ScheduledPostPublisher(db_session, configured, FailingClient(None)).publish(schedule.id)

    log = db_session.query(PublishingLog).one()
    assert log.response_metadata is not None
    assert log.response_metadata["outcome_uncertain"] is True
    with pytest.raises(ApplicationError) as retry_error:
        SchedulingService(db_session, configured).retry_failed(schedule.user_id, schedule.id)
    assert retry_error.value.code == "PUBLISH_OUTCOME_UNCERTAIN"
