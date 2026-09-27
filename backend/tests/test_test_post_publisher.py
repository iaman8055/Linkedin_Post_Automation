import pytest
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus, PublishingStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.post import Post
from app.models.publishing_log import PublishingLog
from app.models.user import User
from app.services.linkedin.client import LinkedInClientError
from app.services.linkedin.token_cipher import TokenCipher
from app.services.publishing.test_post import TestPostPublisher as LinkedInTestPostPublisher
from tests.test_linkedin_service import FakeLinkedInClient


class RateLimitedLinkedInClient(FakeLinkedInClient):
    def create_text_post(
        self,
        *,
        access_token: str,
        member_id: str,
        commentary: str,
        api_version: str,
    ) -> str:
        raise LinkedInClientError("rate limited", 429)


def configured_settings() -> Settings:
    return Settings(
        jwt_secret="publisher-secret-that-is-at-least-32-characters",
        linkedin_client_id="client-id",
        linkedin_client_secret="client-secret",
        linkedin_token_encryption_key=Fernet.generate_key().decode(),
    )


def create_account(db_session: Session, settings: Settings) -> tuple[User, LinkedInAccount]:
    user = User(email="publisher@example.com", password_hash="hashed", display_name="Publisher")
    encryption_key = settings.linkedin_token_encryption_key
    assert encryption_key is not None
    account = LinkedInAccount(
        user=user,
        linkedin_member_id="linkedin-member-123",
        encrypted_access_token=TokenCipher(encryption_key.get_secret_value()).encrypt(
            "real-access-token"
        ),
        scopes="openid profile email w_member_social",
    )
    db_session.add(user)
    db_session.add(account)
    db_session.commit()
    return user, account


def test_test_post_publishing_is_recorded_and_idempotent(db_session: Session) -> None:
    settings = configured_settings()
    user, account = create_account(db_session, settings)
    client = FakeLinkedInClient()
    publisher = LinkedInTestPostPublisher(db_session, settings, client)

    post = publisher.publish(
        user_id=user.id,
        account_id=account.id,
        commentary="A real test post request.",
        idempotency_key="publisher-test-key-0001",
    )
    repeated = publisher.publish(
        user_id=user.id,
        account_id=account.id,
        commentary="A real test post request.",
        idempotency_key="publisher-test-key-0001",
    )

    assert repeated.id == post.id
    assert client.publish_calls == 1
    assert post.status is PostStatus.PUBLISHED
    assert post.linkedin_post_id == "urn:li:share:123456"
    log = db_session.query(PublishingLog).one()
    assert log.status is PublishingStatus.SUCCEEDED


def test_missing_publish_scope_is_rejected(db_session: Session) -> None:
    settings = configured_settings()
    user, account = create_account(db_session, settings)
    account.scopes = "openid profile email"
    db_session.commit()
    publisher = LinkedInTestPostPublisher(db_session, settings, FakeLinkedInClient())

    with pytest.raises(ApplicationError) as error:
        publisher.publish(
            user_id=user.id,
            account_id=account.id,
            commentary="Should not publish.",
            idempotency_key="publisher-test-key-0002",
        )

    assert error.value.code == "LINKEDIN_SCOPE_MISSING"


def test_publish_failure_is_persisted(db_session: Session) -> None:
    settings = configured_settings()
    user, account = create_account(db_session, settings)
    publisher = LinkedInTestPostPublisher(
        db_session, settings, RateLimitedLinkedInClient()
    )

    with pytest.raises(ApplicationError) as error:
        publisher.publish(
            user_id=user.id,
            account_id=account.id,
            commentary="This request is rate limited.",
            idempotency_key="publisher-test-key-0003",
        )

    assert error.value.code == "LINKEDIN_RATE_LIMITED"
    assert db_session.query(Post).one().status is PostStatus.FAILED
    log = db_session.query(PublishingLog).one()
    assert log.status is PublishingStatus.FAILED
    assert log.error_code == "LINKEDIN_HTTP_429"
