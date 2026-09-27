from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.linkedin_account import LinkedInAccount
from app.repositories.base import UserOwnedRepository


class LinkedInAccountRepository(UserOwnedRepository[LinkedInAccount]):
    def __init__(self, session: Session) -> None:
        super().__init__(LinkedInAccount, session)

    def get_by_member(self, user_id: UUID, member_id: str) -> LinkedInAccount | None:
        return self.session.scalar(
            select(LinkedInAccount).where(
                LinkedInAccount.user_id == user_id,
                LinkedInAccount.linkedin_member_id == member_id,
            )
        )

    def get_connected_for_user(self, user_id: UUID) -> LinkedInAccount | None:
        statement = (
            select(LinkedInAccount)
            .where(
                LinkedInAccount.user_id == user_id,
                LinkedInAccount.is_connected.is_(True),
            )
            .order_by(LinkedInAccount.created_at)
            .limit(1)
        )
        return self.session.scalar(statement)
