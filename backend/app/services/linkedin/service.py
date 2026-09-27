import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID, uuid4

import jwt
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.linkedin_account import LinkedInAccount
from app.models.user import User
from app.repositories.linkedin_account import LinkedInAccountRepository
from app.repositories.user import UserRepository
from app.services.linkedin.client import LinkedInClient, LinkedInClientError
from app.services.linkedin.token_cipher import TokenCipher, TokenCipherError

logger = logging.getLogger(__name__)


class LinkedInService:
    def __init__(self, session: Session, settings: Settings, client: LinkedInClient) -> None:
        self.session = session
        self.settings = settings
        self.client = client
        self.accounts = LinkedInAccountRepository(session)
        self.users = UserRepository(session)

    def create_authorization_url(self, user: User) -> str:
        self._require_configuration()
        state = self._create_state(user.id)
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.settings.linkedin_client_id,
                "redirect_uri": self.settings.linkedin_redirect_uri,
                "state": state,
                "scope": " ".join(self.settings.linkedin_oauth_scopes),
            }
        )
        return f"{self.client.authorization_endpoint}?{query}"

    def complete_connection(self, code: str, state: str) -> LinkedInAccount:
        self._require_configuration()
        user_id = self._decode_state(state)
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise ApplicationError("LINKEDIN_OAUTH_STATE_INVALID", "Invalid OAuth state.", 400)

        client_id = self.settings.linkedin_client_id
        client_secret = self.settings.linkedin_client_secret
        encryption_key = self.settings.linkedin_token_encryption_key
        assert client_id is not None and client_secret is not None and encryption_key is not None

        try:
            token = self.client.exchange_code(
                code=code,
                client_id=client_id,
                client_secret=client_secret.get_secret_value(),
                redirect_uri=self.settings.linkedin_redirect_uri,
            )
            profile = self.client.get_user_info(token.access_token)
            cipher = TokenCipher(encryption_key.get_secret_value())
        except (LinkedInClientError, TokenCipherError) as exc:
            logger.warning("linkedin_oauth_failed", extra={"user_id": str(user_id)})
            raise ApplicationError(
                "LINKEDIN_OAUTH_FAILED", "Unable to connect the LinkedIn account.", 502
            ) from exc

        account = self.accounts.get_by_member(user_id, profile.subject)
        if account is None:
            account = LinkedInAccount(
                user_id=user_id,
                linkedin_member_id=profile.subject,
                encrypted_access_token=cipher.encrypt(token.access_token),
            )
            self.accounts.add(account)
        else:
            account.encrypted_access_token = cipher.encrypt(token.access_token)

        account.display_name = profile.name
        account.profile_image_url = profile.picture
        account.encrypted_refresh_token = (
            cipher.encrypt(token.refresh_token) if token.refresh_token else None
        )
        account.token_expires_at = datetime.now(UTC) + timedelta(seconds=token.expires_in)
        account.scopes = token.scope or " ".join(self.settings.linkedin_oauth_scopes)
        account.is_connected = True
        self.session.commit()
        logger.info(
            "linkedin_account_connected",
            extra={"user_id": str(user_id), "linkedin_account_id": str(account.id)},
        )
        return account

    def list_accounts(self, user_id: UUID) -> list[LinkedInAccount]:
        return self.accounts.list_for_user(user_id)

    def disconnect(self, user_id: UUID, account_id: UUID) -> None:
        account = self.accounts.get_for_user(account_id, user_id)
        if account is None:
            raise ApplicationError("LINKEDIN_ACCOUNT_NOT_FOUND", "LinkedIn account not found.", 404)
        account.encrypted_access_token = ""
        account.encrypted_refresh_token = None
        account.token_expires_at = None
        account.scopes = ""
        account.is_connected = False
        self.session.commit()
        logger.info(
            "linkedin_account_disconnected",
            extra={"user_id": str(user_id), "linkedin_account_id": str(account_id)},
        )

    def validate_denied_state(self, state: str) -> UUID:
        return self._decode_state(state)

    def _require_configuration(self) -> None:
        if not self.settings.linkedin_configured:
            raise ApplicationError(
                "LINKEDIN_NOT_CONFIGURED",
                "LinkedIn OAuth is not configured.",
                503,
            )

    def _create_state(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user_id),
                "type": "linkedin_oauth_state",
                "iat": now,
                "exp": now + timedelta(minutes=self.settings.linkedin_oauth_state_expire_minutes),
                "jti": str(uuid4()),
                "iss": self.settings.jwt_issuer,
                "aud": self.settings.jwt_audience,
            },
            self.settings.jwt_secret.get_secret_value(),
            algorithm=self.settings.jwt_algorithm,
        )

    def _decode_state(self, state: str) -> UUID:
        try:
            payload = jwt.decode(
                state,
                self.settings.jwt_secret.get_secret_value(),
                algorithms=[self.settings.jwt_algorithm],
                audience=self.settings.jwt_audience,
                issuer=self.settings.jwt_issuer,
                options={"require": ["sub", "type", "iat", "exp", "jti"]},
            )
            if payload.get("type") != "linkedin_oauth_state":
                raise ValueError("Unexpected state type")
            return UUID(str(payload["sub"]))
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise ApplicationError(
                "LINKEDIN_OAUTH_STATE_INVALID", "Invalid OAuth state.", 400
            ) from exc

