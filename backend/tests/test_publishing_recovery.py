from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import PostStatus, PublishingStatus, ScheduleStatus
from app.models.post import Post
from app.models.publishing_log import PublishingLog
from app.models.schedule import Schedule
from app.models.user import User
from app.services.publishing.recovery import PublishingRecoveryService


def stale_schedule(session: Session, email: str) -> Schedule:
    user = User(email=email, password_hash="hashed", display_name="Recovery")
    post = Post(user=user, content="Recover me", status=PostStatus.PUBLISHING)
    schedule = Schedule(
        user=user,
        post=post,
        status=ScheduleStatus.ACTIVE,
        scheduled_for=datetime.now(UTC) - timedelta(hours=1),
        next_run_at=datetime.now(UTC) - timedelta(hours=1),
        last_attempt_at=datetime.now(UTC) - timedelta(minutes=30),
        attempt_count=1,
    )
    session.add_all([user, post, schedule])
    session.commit()
    return schedule


def test_stale_claim_before_external_attempt_is_requeued(db_session: Session) -> None:
    schedule = stale_schedule(db_session, "recovery-safe@example.com")
    result = PublishingRecoveryService(
        db_session, Settings(publishing_stale_claim_minutes=15)
    ).recover_stale_claims()

    assert result == {"requeued": 1, "uncertain": 0, "completed": 0}
    assert schedule.post.status is PostStatus.SCHEDULED
    assert schedule.status is ScheduleStatus.ACTIVE


def test_stale_claim_after_attempt_is_marked_uncertain(db_session: Session) -> None:
    schedule = stale_schedule(db_session, "recovery-uncertain@example.com")
    log = PublishingLog(
        user_id=schedule.user_id,
        post_id=schedule.post_id,
        status=PublishingStatus.STARTED,
        attempt_number=1,
        idempotency_key="c" * 64,
    )
    db_session.add(log)
    db_session.commit()

    result = PublishingRecoveryService(
        db_session, Settings(publishing_stale_claim_minutes=15)
    ).recover_stale_claims()

    assert result == {"requeued": 0, "uncertain": 1, "completed": 0}
    assert schedule.post.status is PostStatus.FAILED
    assert schedule.status is ScheduleStatus.COMPLETED
    assert log.status is PublishingStatus.FAILED
    assert log.error_code == "PUBLISH_WORKER_INTERRUPTED"
    assert log.response_metadata is not None
    assert log.response_metadata["retry_safe"] is False
