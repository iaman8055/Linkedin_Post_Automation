from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.linkedin_account import LinkedInAccount
from app.repositories.base import UserOwnedRepository


class LinkedInAccountRepository(UserOwnedRepository[LinkedInAccount]):
    def __init__(self, session: Session) -> None:
        super().__init__(LinkedInAccount, session)

    def get_by_member(
        self, user_id: UUID, member_id: str, workspace_id: UUID | None = None
    ) -> LinkedInAccount | None:
        workspace_filter = (
            LinkedInAccount.workspace_id == workspace_id
            if workspace_id is not None else LinkedInAccount.workspace_id.is_(None)
        )
        return self.session.scalar(
            select(LinkedInAccount).where(
                LinkedInAccount.user_id == user_id,
                LinkedInAccount.linkedin_member_id == member_id,
                workspace_filter,
            )
        )

    def get_connected_for_user(
        self, user_id: UUID, workspace_id: UUID | None = None
    ) -> LinkedInAccount | None:
        filters = [
            LinkedInAccount.user_id == user_id,
            LinkedInAccount.is_connected.is_(True),
        ]
        if workspace_id is not None:
            filters.append(or_(
                LinkedInAccount.workspace_id == workspace_id,
                LinkedInAccount.workspace_id.is_(None),
            ))
        statement = (
            select(LinkedInAccount)
            .where(*filters)
            .order_by(LinkedInAccount.created_at)
            .limit(1)
        )
        return self.session.scalar(statement)

    def list_for_workspace(self, user_id: UUID, workspace_id: UUID) -> list[LinkedInAccount]:
        return list(self.session.scalars(select(LinkedInAccount).where(
            LinkedInAccount.user_id == user_id,
            or_(
                LinkedInAccount.workspace_id == workspace_id,
                LinkedInAccount.workspace_id.is_(None),
            ),
        )))
