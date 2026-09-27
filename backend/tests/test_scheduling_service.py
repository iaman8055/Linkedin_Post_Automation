from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import PostStatus, ScheduleRecurrence, ScheduleStatus
from app.models.post import Post
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.services.scheduling import SchedulingService


def create_approved_post(
    session: Session, email: str = "schedule@example.com"
) -> tuple[User, Post]:
    user = User(email=email, password_hash="hashed", display_name="Scheduler")
    post = Post(user=user, content="A reviewed post", status=PostStatus.APPROVED)
    session.add_all([user, post])
    session.commit()
    return user, post


def test_schedule_lifecycle_updates_post_and_uses_utc(db_session: Session) -> None:
    user, post = create_approved_post(db_session)
    service = SchedulingService(db_session)
    future = datetime.now(UTC) + timedelta(days=2)

    schedule = service.create(
        user.id,
        ScheduleCreate(
            post_id=post.id,
            scheduled_for=future,
            timezone="Asia/Calcutta",
            recurrence=ScheduleRecurrence.ONCE,
        ),
    )
    assert schedule.status is ScheduleStatus.ACTIVE
    assert schedule.next_run_at is not None
    assert schedule.next_run_at.replace(tzinfo=UTC) == future
    assert post.status is PostStatus.SCHEDULED

    paused = service.pause(user.id, schedule.id)
    assert paused.status is ScheduleStatus.PAUSED
    assert paused.next_run_at is None

    new_time = future + timedelta(days=1)
    changed = service.reschedule(
        user.id, schedule.id, ScheduleUpdate(scheduled_for=new_time, timezone="UTC")
    )
    assert changed.next_run_at is None
    assert changed.scheduled_for.replace(tzinfo=UTC) == new_time

    resumed = service.resume(user.id, schedule.id)
    assert resumed.next_run_at is not None
    assert resumed.next_run_at.replace(tzinfo=UTC) == new_time
    cancelled = service.cancel(user.id, schedule.id)
    assert cancelled.status is ScheduleStatus.CANCELLED
    refreshed_post = db_session.get(Post, post.id)
    assert refreshed_post is not None
    assert refreshed_post.status == PostStatus.APPROVED


def test_schedule_rejects_unapproved_past_and_duplicate_posts(db_session: Session) -> None:
    user, post = create_approved_post(db_session, "schedule-validation@example.com")
    service = SchedulingService(db_session)
    post.status = PostStatus.DRAFT
    db_session.commit()
    with pytest.raises(ApplicationError) as unapproved:
        service.create(
            user.id,
            ScheduleCreate(post_id=post.id, scheduled_for=datetime.now(UTC) + timedelta(days=1)),
        )
    assert unapproved.value.code == "POST_NOT_APPROVED"

    post.status = PostStatus.APPROVED
    db_session.commit()
    with pytest.raises(ApplicationError) as past:
        service.create(
            user.id,
            ScheduleCreate(post_id=post.id, scheduled_for=datetime.now(UTC) - timedelta(minutes=1)),
        )
    assert past.value.code == "SCHEDULE_IN_PAST"

    payload = ScheduleCreate(post_id=post.id, scheduled_for=datetime.now(UTC) + timedelta(days=1))
    service.create(user.id, payload)
    post.status = PostStatus.APPROVED
    db_session.commit()
    with pytest.raises(ApplicationError) as duplicate:
        service.create(user.id, payload)
    assert duplicate.value.code == "POST_ALREADY_SCHEDULED"


def test_schedules_are_user_scoped(db_session: Session) -> None:
    owner, post = create_approved_post(db_session, "schedule-owner@example.com")
    other = User(email="schedule-other@example.com", password_hash="hashed", display_name="Other")
    db_session.add(other)
    db_session.commit()
    schedule = SchedulingService(db_session).create(
        owner.id,
        ScheduleCreate(post_id=post.id, scheduled_for=datetime.now(UTC) + timedelta(days=1)),
    )

    with pytest.raises(ApplicationError) as hidden:
        SchedulingService(db_session).get(other.id, schedule.id)
    assert hidden.value.code == "SCHEDULE_NOT_FOUND"
