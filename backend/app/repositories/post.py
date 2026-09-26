from sqlalchemy.orm import Session

from app.models.post import Post
from app.repositories.base import UserOwnedRepository


class PostRepository(UserOwnedRepository[Post]):
    def __init__(self, session: Session) -> None:
        super().__init__(Post, session)

