import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.auth_token import AuthToken
from app.models.enums import AuthTokenKind
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.auth_token import AuthTokenRepository
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.tokens = AuthTokenRepository(session)

    def register(self, email: str, password: str, display_name: str) -> tuple[User, TokenPair]:
        normalized_email = email.strip().lower()
        if self.users.get_by_email(normalized_email) is not None:
            raise ApplicationError("EMAIL_ALREADY_REGISTERED", "An account already exists.", 409)

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        user.settings = UserSettings()
        self.users.add(user)
        self.issue_action_token(user, AuthTokenKind.EMAIL_VERIFICATION)
        pair = self._create_token_pair(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApplicationError(
                "EMAIL_ALREADY_REGISTERED", "An account already exists.", 409
            ) from exc
        logger.info("user_registered", extra={"user_id": str(user.id)})
        return user, pair

    def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = self.users.get_by_email(email.strip().lower())
        password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        password_matches = verify_password(password, password_hash)
        if user is None or not password_matches:
            raise ApplicationError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        if not user.is_active:
            raise ApplicationError("ACCOUNT_DISABLED", "This account is disabled.", 403)

        pair = self._create_token_pair(user)
        self.session.commit()
        logger.info("user_logged_in", extra={"user_id": str(user.id)})
        return user, pair

    def refresh(self, raw_token: str) -> tuple[User, TokenPair]:
        token = self.tokens.get_by_hash_for_update(hash_opaque_token(raw_token, self.settings))
        now = datetime.now(UTC)
        if token is None or token.kind is not AuthTokenKind.REFRESH:
            raise ApplicationError("INVALID_REFRESH_TOKEN", "Invalid refresh token.", 401)
        if token.consumed_at is not None:
            self.tokens.revoke_family(token.family_id, now)
            self.session.commit()
            logger.warning("refresh_token_reuse", extra={"user_id": str(token.user_id)})
            raise ApplicationError("REFRESH_TOKEN_REUSED", "Refresh token reuse detected.", 401)
        if token.revoked_at is not None or self._is_expired(token.expires_at, now):
            raise ApplicationError("INVALID_REFRESH_TOKEN", "Invalid refresh token.", 401)
        if not token.user.is_active:
            raise ApplicationError("ACCOUNT_DISABLED", "This account is disabled.", 403)

        token.consumed_at = now
        pair, replacement = self._create_token_pair_with_record(token.user, token.family_id)
        token.replaced_by = replacement
        self.session.commit()
        return token.user, pair

    def logout(self, raw_token: str) -> None:
        token = self.tokens.get_by_hash_for_update(hash_opaque_token(raw_token, self.settings))
        if token is not None and token.kind is AuthTokenKind.REFRESH:
            self.tokens.revoke_family(token.family_id, datetime.now(UTC))
            self.session.commit()

    def issue_action_token(self, user: User, kind: AuthTokenKind) -> str:
        if kind is AuthTokenKind.REFRESH:
            raise ValueError("Use token-pair issuance for refresh tokens")
        now = datetime.now(UTC)
        expiry = (
            now + timedelta(hours=self.settings.email_verification_token_expire_hours)
            if kind is AuthTokenKind.EMAIL_VERIFICATION
            else now + timedelta(minutes=self.settings.password_reset_token_expire_minutes)
        )
        raw_token = generate_opaque_token()
        self.tokens.add(
            AuthToken(
                user=user,
                kind=kind,
                token_hash=hash_opaque_token(raw_token, self.settings),
                expires_at=expiry,
            )
        )
        return raw_token

    def request_password_reset(self, email: str) -> tuple[User, str] | None:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            return None
        token = self.issue_action_token(user, AuthTokenKind.PASSWORD_RESET)
        self.session.commit()
        return user, token

    def verify_email(self, raw_token: str) -> User:
        token = self._consume_action_token(raw_token, AuthTokenKind.EMAIL_VERIFICATION)
        token.user.is_verified = True
        token.user.email_verified_at = datetime.now(UTC)
        self.session.commit()
        return token.user

    def reset_password(self, raw_token: str, new_password: str) -> User:
        token = self._consume_action_token(raw_token, AuthTokenKind.PASSWORD_RESET)
        token.user.password_hash = hash_password(new_password)
        self.tokens.revoke_user_refresh_tokens(token.user_id, datetime.now(UTC))
        self.session.commit()
        logger.info("password_reset", extra={"user_id": str(token.user_id)})
        return token.user

    def _consume_action_token(self, raw_token: str, kind: AuthTokenKind) -> AuthToken:
        token = self.tokens.get_by_hash_for_update(hash_opaque_token(raw_token, self.settings))
        now = datetime.now(UTC)
        if (
            token is None
            or token.kind is not kind
            or token.consumed_at is not None
            or token.revoked_at is not None
            or self._is_expired(token.expires_at, now)
        ):
            raise ApplicationError("INVALID_ACTION_TOKEN", "Invalid or expired token.", 400)
        token.consumed_at = now
        return token

    def _create_token_pair(self, user: User) -> TokenPair:
        pair, _ = self._create_token_pair_with_record(user)
        return pair

    def _create_token_pair_with_record(
        self, user: User, family_id: UUID | None = None
    ) -> tuple[TokenPair, AuthToken]:
        access_token, expires_in = create_access_token(user.id, self.settings)
        raw_refresh = generate_opaque_token()
        record = AuthToken(
            user=user,
            kind=AuthTokenKind.REFRESH,
            token_hash=hash_opaque_token(raw_refresh, self.settings),
            expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days),
        )
        if family_id is not None:
            record.family_id = family_id
        self.tokens.add(record)
        return TokenPair(access_token, raw_refresh, expires_in), record

    @staticmethod
    def _is_expired(expires_at: datetime, now: datetime) -> bool:
        comparable = expires_at if expires_at.tzinfo is not None else expires_at.replace(tzinfo=UTC)
        return comparable <= now
