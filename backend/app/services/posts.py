from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import PostStatus
from app.models.post import Post
from app.repositories.post import PostRepository
from app.schemas.post import PostCreate, PostUpdate


class PostService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.posts = PostRepository(session)

    def create(self, user_id: UUID, payload: PostCreate) -> Post:
        post = self.posts.create_for_user(
            user_id,
            title=self._normalize_optional_title(payload.title),
            content=payload.content,
            language=payload.language,
            status=PostStatus.DRAFT,
            content_fingerprint=self._fingerprint(payload.content),
        )
        self.session.commit()
        self.session.refresh(post)
        return post

    def list(
        self,
        user_id: UUID,
        *,
        status: PostStatus | None,
        search: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Post], int]:
        normalized_search = search.strip() if search else None
        return self.posts.list_filtered_for_user(
            user_id,
            status=status,
            search=normalized_search,
            offset=offset,
            limit=limit,
        )

    def get(self, user_id: UUID, post_id: UUID) -> Post:
        post = self.posts.get_for_user(post_id, user_id)
        if post is None:
            raise ApplicationError("POST_NOT_FOUND", "Post not found.", 404)
        return post

    def update(self, user_id: UUID, post_id: UUID, payload: PostUpdate) -> Post:
        post = self.get(user_id, post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError("POST_NOT_EDITABLE", "Only draft posts can be edited.", 409)
        changes = payload.model_dump(exclude_unset=True)
        if "title" in changes:
            post.title = self._normalize_optional_title(changes["title"])
        if "content" in changes:
            post.content = changes["content"]
            post.content_fingerprint = self._fingerprint(post.content)
        if "language" in changes:
            post.language = changes["language"]
        self.session.commit()
        self.session.refresh(post)
        return post

    def delete(self, user_id: UUID, post_id: UUID) -> None:
        post = self.get(user_id, post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError("POST_NOT_DELETABLE", "Only draft posts can be deleted.", 409)
        self.posts.delete(post)
        self.session.commit()

    def approve(self, user_id: UUID, post_id: UUID) -> Post:
        post = self.get(user_id, post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError("POST_NOT_APPROVABLE", "Only draft posts can be approved.", 409)
        post.status = PostStatus.APPROVED
        post.approved_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(post)
        return post

    def return_to_draft(self, user_id: UUID, post_id: UUID) -> Post:
        post = self.get(user_id, post_id)
        if post.status != PostStatus.APPROVED:
            raise ApplicationError(
                "POST_NOT_RETURNABLE_TO_DRAFT", "Only approved posts can return to draft.", 409
            )
        post.status = PostStatus.DRAFT
        post.approved_at = None
        self.session.commit()
        self.session.refresh(post)
        return post

    @staticmethod
    def _normalize_optional_title(title: str | None) -> str | None:
        if title is None:
            return None
        normalized = title.strip()
        return normalized or None

    @staticmethod
    def _fingerprint(content: str) -> str:
        return sha256(content.encode("utf-8")).hexdigest()
