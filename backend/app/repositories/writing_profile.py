from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.writing_profile import WritingProfile
from app.repositories.base import UserOwnedRepository


class WritingProfileRepository(UserOwnedRepository[WritingProfile]):
    def __init__(self, session: Session) -> None:
        super().__init__(WritingProfile, session)

    def list_with_total(self, user_id: UUID) -> tuple[list[WritingProfile], int]:
        filters = (WritingProfile.user_id == user_id,)
        total = self.session.scalar(
            select(func.count()).select_from(WritingProfile).where(*filters)
        ) or 0
        statement = select(WritingProfile).where(*filters).order_by(
            WritingProfile.is_default.desc(), WritingProfile.updated_at.desc()
        )
        return list(self.session.scalars(statement)), total

    def clear_default(self, user_id: UUID, *, except_id: UUID | None = None) -> None:
        statement = update(WritingProfile).where(WritingProfile.user_id == user_id)
        if except_id is not None:
            statement = statement.where(WritingProfile.id != except_id)
        self.session.execute(statement.values(is_default=False))
