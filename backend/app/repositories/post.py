from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import PostStatus
from app.models.post import Post
from app.repositories.base import UserOwnedRepository


class PostRepository(UserOwnedRepository[Post]):
    def __init__(self, session: Session) -> None:
        super().__init__(Post, session)

    def list_filtered_for_user(
        self,
        user_id: UUID,
        *,
        status: PostStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Post], int]:
        filters = [Post.user_id == user_id]
        if status is not None:
            filters.append(Post.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))

        items_statement = (
            select(Post)
            .where(*filters)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count()).select_from(Post).where(*filters)
        items = list(self.session.scalars(items_statement))
        total = self.session.scalar(count_statement) or 0
        return items, total

    def list_for_campaign(
        self,
        user_id: UUID,
        campaign_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Post], int]:
        filters = [Post.user_id == user_id, Post.campaign_id == campaign_id]
        statement = (
            select(Post)
            .where(*filters)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count()).select_from(Post).where(*filters)
        return (
            list(self.session.scalars(statement)),
            self.session.scalar(count_statement) or 0,
        )
