from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.post_media import PostMedia
from app.repositories.base import UserOwnedRepository


class PostMediaRepository(UserOwnedRepository[PostMedia]):
    def __init__(self, session: Session) -> None:
        super().__init__(PostMedia, session)

    def list_for_post(self, user_id: UUID, post_id: UUID) -> list[PostMedia]:
        return list(self.session.scalars(
            select(PostMedia).where(
                PostMedia.user_id == user_id, PostMedia.post_id == post_id
            ).order_by(PostMedia.position, PostMedia.created_at)
        ))

    def count_for_post(self, user_id: UUID, post_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(PostMedia).where(
                PostMedia.user_id == user_id, PostMedia.post_id == post_id
            )
        ) or 0
