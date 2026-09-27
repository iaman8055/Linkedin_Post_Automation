from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.user import User
from app.services.linkedin.client import (
    LinkedInClient,
    LinkedInTokenResponse,
    LinkedInUserInfo,
)
from app.services.linkedin.service import LinkedInService
from app.services.linkedin.token_cipher import TokenCipher


class FakeLinkedInClient(LinkedInClient):
    def __init__(self) -> None:
        super().__init__()
        self.publish_calls = 0

    def exchange_code(
        self,
        *,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> LinkedInTokenResponse:
        assert code == "authorization-code"
        assert client_id == "linkedin-client-id"
        assert client_secret == "linkedin-client-secret"
        assert redirect_uri.endswith("/api/v1/linkedin/callback")
        return LinkedInTokenResponse(
            access_token="real-access-token",
            expires_in=3600,
            scope="openid profile email w_member_social",
        )

    def get_user_info(self, access_token: str) -> LinkedInUserInfo:
        assert access_token == "real-access-token"
        return LinkedInUserInfo(
            subject="linkedin-member-123",
            name="LinkedIn Member",
            picture="https://example.com/photo.jpg",
            email="member@example.com",
            email_verified=True,
        )

    def create_text_post(
        self,
        *,
        access_token: str,
        member_id: str,
        commentary: str,
        api_version: str,
    ) -> str:
        self.publish_calls += 1
        assert access_token == "real-access-token"
        assert member_id == "linkedin-member-123"
        assert commentary
        assert api_version == "202609"
        return "urn:li:share:123456"


@pytest.fixture
def linkedin_settings() -> Settings:
    return Settings(
        jwt_secret="test-secret-that-is-at-least-32-characters",
        linkedin_client_id="linkedin-client-id",
        linkedin_client_secret="linkedin-client-secret",
        linkedin_token_encryption_key=Fernet.generate_key().decode(),
    )


def test_oauth_connection_encrypts_tokens(
    db_session: Session, linkedin_settings: Settings
) -> None:
    user = User(email="linkedin@example.com", password_hash="hashed", display_name="Member")
    db_session.add(user)
    db_session.commit()
    service = LinkedInService(db_session, linkedin_settings, FakeLinkedInClient())

    authorization_url = service.create_authorization_url(user)
    query = parse_qs(urlparse(authorization_url).query)
    assert query["scope"] == ["openid profile email w_member_social"]
    assert query["client_id"] == ["linkedin-client-id"]

    account = service.complete_connection("authorization-code", query["state"][0])
    assert account.linkedin_member_id == "linkedin-member-123"
    assert account.encrypted_access_token != "real-access-token"
    cipher = TokenCipher(
        linkedin_settings.linkedin_token_encryption_key.get_secret_value()  # type: ignore[union-attr]
    )
    assert cipher.decrypt(account.encrypted_access_token) == "real-access-token"
    assert account.is_connected

    service.disconnect(user.id, account.id)
    assert not account.is_connected
    assert account.encrypted_access_token == ""


def test_invalid_state_is_rejected(db_session: Session, linkedin_settings: Settings) -> None:
    service = LinkedInService(db_session, linkedin_settings, FakeLinkedInClient())

    with pytest.raises(ApplicationError) as error:
        service.complete_connection("authorization-code", "tampered-state")

    assert error.value.code == "LINKEDIN_OAUTH_STATE_INVALID"


def test_unconfigured_linkedin_is_explicitly_unavailable(db_session: Session) -> None:
    settings = Settings(
        linkedin_client_id=None,
        linkedin_client_secret=None,
        linkedin_token_encryption_key=None,
    )
    service = LinkedInService(db_session, settings, FakeLinkedInClient())
    user = User(email="user@example.com", password_hash="hashed", display_name="User")

    with pytest.raises(ApplicationError) as error:
        service.create_authorization_url(user)

    assert error.value.code == "LINKEDIN_NOT_CONFIGURED"
