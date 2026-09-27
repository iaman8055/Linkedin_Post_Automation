from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.auth_token import AuthToken
from app.models.enums import AuthTokenKind
from app.repositories.base import BaseRepository


class AuthTokenRepository(BaseRepository[AuthToken]):
    def __init__(self, session: Session) -> None:
        super().__init__(AuthToken, session)

    def get_by_hash(self, token_hash: str) -> AuthToken | None:
        return self.session.scalar(select(AuthToken).where(AuthToken.token_hash == token_hash))

    def get_by_hash_for_update(self, token_hash: str) -> AuthToken | None:
        statement = select(AuthToken).where(AuthToken.token_hash == token_hash).with_for_update()
        return self.session.scalar(statement)

    def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        self.session.execute(
            update(AuthToken)
            .where(AuthToken.family_id == family_id, AuthToken.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )

    def revoke_user_refresh_tokens(self, user_id: UUID, revoked_at: datetime) -> None:
        self.session.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.kind == AuthTokenKind.REFRESH,
                AuthToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
