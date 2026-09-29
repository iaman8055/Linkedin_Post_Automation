from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import TemplateStatus
from app.models.template import Template
from app.repositories.base import UserOwnedRepository


class TemplateRepository(UserOwnedRepository[Template]):
    def __init__(self, session: Session) -> None:
        super().__init__(Template, session)

    def list_filtered_for_user(
        self,
        user_id: UUID,
        *,
        status: TemplateStatus | None,
        search: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Template], int]:
        filters = self.ownership_filters(user_id)
        if status is not None:
            filters.append(Template.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(or_(Template.name.ilike(pattern), Template.description.ilike(pattern)))
        count = self.session.scalar(select(func.count()).select_from(Template).where(*filters)) or 0
        statement = (
            select(Template)
            .where(*filters)
            .order_by(Template.updated_at.desc(), Template.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement)), count
