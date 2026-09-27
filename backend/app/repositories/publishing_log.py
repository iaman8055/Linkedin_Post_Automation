from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.publishing_log import PublishingLog
from app.repositories.base import BaseRepository


class PublishingLogRepository(BaseRepository[PublishingLog]):
    def __init__(self, session: Session) -> None:
        super().__init__(PublishingLog, session)

    def get_by_idempotency_key(self, idempotency_key: str) -> PublishingLog | None:
        return self.session.scalar(
            select(PublishingLog).where(PublishingLog.idempotency_key == idempotency_key)
        )

    def get_attempt(self, post_id: UUID, attempt_number: int) -> PublishingLog | None:
        return self.session.scalar(
            select(PublishingLog).where(
                PublishingLog.post_id == post_id,
                PublishingLog.attempt_number == attempt_number,
            )
        )

    def latest_for_post(self, post_id: UUID) -> PublishingLog | None:
        statement = (
            select(PublishingLog)
            .where(PublishingLog.post_id == post_id)
            .order_by(PublishingLog.attempt_number.desc())
            .limit(1)
        )
        return self.session.scalar(statement)
