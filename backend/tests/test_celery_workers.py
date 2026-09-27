from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth_token import AuthToken
from app.models.enums import AuthTokenKind, PostStatus, ScheduleStatus
from app.models.post import Post
from app.models.schedule import Schedule
from app.models.user import User
from workers import publishing_tasks, system_tasks
from workers.celery_app import celery_app


def session_context(session: Session) -> Callable[[], AbstractContextManager[Session]]:
    @contextmanager
    def context() -> Iterator[Session]:
        yield session

    return context


def test_celery_queues_routes_and_beat_are_configured() -> None:
    queue_names = {queue.name for queue in celery_app.conf.task_queues}
    assert queue_names == {
        "default",
        "publishing",
        "ai",
        "research",
        "analytics",
        "notifications",
    }
    assert celery_app.conf.task_routes["workers.ai_tasks.*"]["queue"] == "ai"
    assert (
        celery_app.conf.beat_schedule["remove-expired-auth-tokens"]["task"]
        == "workers.system_tasks.remove_expired_auth_tokens"
    )
    assert (
        celery_app.conf.beat_schedule["dispatch-due-linkedin-posts"]["task"]
        == "workers.publishing_tasks.dispatch_due_schedules"
    )


def test_beat_cleanup_removes_only_expired_tokens(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = User(email="worker-auth@example.com", password_hash="hashed", display_name="Worker")
    db_session.add(user)
    db_session.flush()
    expired = AuthToken(
        user_id=user.id,
        kind=AuthTokenKind.REFRESH,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    active = AuthToken(
        user_id=user.id,
        kind=AuthTokenKind.REFRESH,
        token_hash="b" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    db_session.add_all([expired, active])
    db_session.commit()
    monkeypatch.setattr(system_tasks, "worker_session", session_context(db_session))

    removed = system_tasks.remove_expired_auth_tokens.run()

    assert removed == 1
    assert list(db_session.scalars(select(AuthToken.token_hash))) == [active.token_hash]


def test_publishing_boundary_reads_due_schedules_without_mutation(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = User(email="worker-due@example.com", password_hash="hashed", display_name="Worker")
    due_post = Post(user=user, content="Due", status=PostStatus.SCHEDULED)
    future_post = Post(user=user, content="Later", status=PostStatus.SCHEDULED)
    db_session.add_all([user, due_post, future_post])
    db_session.flush()
    due = Schedule(
        user_id=user.id,
        post_id=due_post.id,
        status=ScheduleStatus.ACTIVE,
        scheduled_for=datetime.now(UTC) - timedelta(minutes=2),
        next_run_at=datetime.now(UTC) - timedelta(minutes=2),
    )
    future = Schedule(
        user_id=user.id,
        post_id=future_post.id,
        status=ScheduleStatus.ACTIVE,
        scheduled_for=datetime.now(UTC) + timedelta(hours=2),
        next_run_at=datetime.now(UTC) + timedelta(hours=2),
    )
    db_session.add_all([due, future])
    db_session.commit()
    monkeypatch.setattr(publishing_tasks, "worker_session", session_context(db_session))

    assert publishing_tasks.list_due_schedule_ids.run() == [str(due.id)]
    assert due.status is ScheduleStatus.ACTIVE
    assert future.status is ScheduleStatus.ACTIVE


def test_dispatch_claims_due_schedule_and_enqueues_publish(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = User(email="worker-dispatch@example.com", password_hash="hashed", display_name="Worker")
    post = Post(user=user, content="Dispatch me", status=PostStatus.SCHEDULED)
    schedule = Schedule(
        user=user,
        post=post,
        status=ScheduleStatus.ACTIVE,
        scheduled_for=datetime.now(UTC) - timedelta(minutes=1),
        next_run_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    db_session.add_all([user, post, schedule])
    db_session.commit()
    monkeypatch.setattr(publishing_tasks, "worker_session", session_context(db_session))
    calls: list[tuple[list[str], str]] = []

    def capture(*, args: list[str], queue: str) -> None:
        calls.append((args, queue))

    monkeypatch.setattr(publishing_tasks.publish_scheduled_post, "apply_async", capture)

    assert publishing_tasks.dispatch_due_schedules.run() == [str(schedule.id)]
    assert calls == [([str(schedule.id)], "publishing")]
    assert post.status is PostStatus.PUBLISHING
    assert schedule.attempt_count == 1
    assert schedule.last_attempt_at is not None
