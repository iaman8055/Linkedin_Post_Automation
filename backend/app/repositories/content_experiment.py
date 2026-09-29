from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_experiment import ContentExperiment
from app.repositories.base import UserOwnedRepository


class ContentExperimentRepository(UserOwnedRepository[ContentExperiment]):
    def __init__(self, session: Session) -> None:
        super().__init__(ContentExperiment, session)

    def list_for_user_with_posts(self, user_id: UUID) -> list[ContentExperiment]:
        return list(self.session.scalars(
            select(ContentExperiment).where(*self.ownership_filters(user_id))
            .options(
                selectinload(ContentExperiment.version_a),
                selectinload(ContentExperiment.version_b),
            ).order_by(ContentExperiment.created_at.desc())
        ))
