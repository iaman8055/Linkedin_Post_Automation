import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.core.security import verify_password
from app.models.enums import AuthTokenKind
from app.services.auth import AuthService


@pytest.fixture
def auth_service(db_session: Session) -> AuthService:
    return AuthService(db_session, Settings(jwt_secret="test-secret-that-is-at-least-32-bytes"))


def test_register_login_refresh_and_reuse_detection(auth_service: AuthService) -> None:
    user, initial = auth_service.register(
        "Author@Example.com", "strong-password-123", "Author"
    )

    assert user.email == "author@example.com"
    assert user.password_hash != "strong-password-123"
    assert verify_password("strong-password-123", user.password_hash)

    logged_in_user, login_pair = auth_service.login("author@example.com", "strong-password-123")
    assert logged_in_user.id == user.id

    _, rotated = auth_service.refresh(login_pair.refresh_token)
    assert rotated.refresh_token != login_pair.refresh_token

    with pytest.raises(ApplicationError) as error:
        auth_service.refresh(login_pair.refresh_token)
    assert error.value.code == "REFRESH_TOKEN_REUSED"

    auth_service.logout(initial.refresh_token)
    with pytest.raises(ApplicationError):
        auth_service.refresh(initial.refresh_token)


def test_email_verification_and_password_reset(auth_service: AuthService) -> None:
    user, pair = auth_service.register(
        "verify@example.com", "original-password-123", "Verify User"
    )
    verification_token = auth_service.issue_action_token(user, AuthTokenKind.EMAIL_VERIFICATION)
    auth_service.session.commit()

    verified_user = auth_service.verify_email(verification_token)
    assert verified_user.is_verified
    assert verified_user.email_verified_at is not None

    reset_request = auth_service.request_password_reset(user.email)
    assert reset_request is not None
    _, reset_token = reset_request
    auth_service.reset_password(reset_token, "replacement-password-456")
    assert verify_password("replacement-password-456", user.password_hash)

    with pytest.raises(ApplicationError):
        auth_service.refresh(pair.refresh_token)


def test_invalid_credentials_use_generic_error(auth_service: AuthService) -> None:
    with pytest.raises(ApplicationError) as error:
        auth_service.login("missing@example.com", "not-the-password")

    assert error.value.code == "INVALID_CREDENTIALS"
