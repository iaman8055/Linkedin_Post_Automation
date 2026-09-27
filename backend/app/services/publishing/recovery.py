import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import PostStatus, PublishingStatus, ScheduleStatus
from app.repositories.publishing_log import PublishingLogRepository
from app.repositories.schedule import ScheduleRepository

logger = logging.getLogger(__name__)


class PublishingRecoveryService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.schedules = ScheduleRepository(session)
        self.logs = PublishingLogRepository(session)

    def recover_stale_claims(self, *, limit: int = 100) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(
            minutes=self.settings.publishing_stale_claim_minutes
        )
        schedules = self.schedules.claim_stale_publishing(cutoff, limit=limit)
        requeued = 0
        uncertain = 0
        completed = 0
        for schedule in schedules:
            log = self.logs.get_attempt(schedule.post_id, schedule.attempt_count)
            if log is None:
                schedule.post.status = PostStatus.SCHEDULED
                schedule.next_run_at = datetime.now(UTC)
                requeued += 1
            elif log.status == PublishingStatus.SUCCEEDED and log.external_post_id:
                schedule.post.status = PostStatus.PUBLISHED
                schedule.post.linkedin_post_id = log.external_post_id
                schedule.post.published_at = datetime.now(UTC)
                schedule.status = ScheduleStatus.COMPLETED
                schedule.next_run_at = None
                completed += 1
            else:
                schedule.post.status = PostStatus.FAILED
                schedule.status = ScheduleStatus.COMPLETED
                schedule.next_run_at = None
                if log.status == PublishingStatus.STARTED:
                    log.status = PublishingStatus.FAILED
                    log.error_code = "PUBLISH_WORKER_INTERRUPTED"
                    log.error_message = "Publishing worker stopped before confirming the result."
                log.response_metadata = {
                    **(log.response_metadata or {}),
                    "retry_safe": False,
                    "outcome_uncertain": True,
                    "automatic_retry_scheduled": False,
                }
                uncertain += 1
        self.session.commit()
        if schedules:
            logger.warning(
                "stale_publishing_claims_recovered",
                extra={
                    "requeued": requeued,
                    "uncertain": uncertain,
                    "completed": completed,
                },
            )
        return {"requeued": requeued, "uncertain": uncertain, "completed": completed}
