from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_plan import ContentPlan
from app.repositories.base import UserOwnedRepository


class ContentPlanRepository(UserOwnedRepository[ContentPlan]):
    def __init__(self, session: Session) -> None:
        super().__init__(ContentPlan, session)

    def get_with_items(self, plan_id: UUID, user_id: UUID) -> ContentPlan | None:
        return self.session.scalar(
            select(ContentPlan)
            .where(ContentPlan.id == plan_id, ContentPlan.user_id == user_id)
            .options(selectinload(ContentPlan.items))
        )

    def list_with_items(self, user_id: UUID) -> list[ContentPlan]:
        return list(self.session.scalars(
            select(ContentPlan).where(ContentPlan.user_id == user_id)
            .options(selectinload(ContentPlan.items))
            .order_by(ContentPlan.created_at.desc())
        ))
