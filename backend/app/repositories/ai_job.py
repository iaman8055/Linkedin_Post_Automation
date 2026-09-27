from sqlalchemy.orm import Session

from app.models.ai_job import AIJob
from app.repositories.base import UserOwnedRepository


class AIJobRepository(UserOwnedRepository[AIJob]):
    def __init__(self, session: Session) -> None:
        super().__init__(AIJob, session)

