from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import delete
from sqlalchemy.engine import CursorResult

from app.models.auth_token import AuthToken
from workers.celery_app import celery_app
from workers.database import worker_session


@celery_app.task(  # type: ignore[untyped-decorator]
    name="workers.system_tasks.remove_expired_auth_tokens"
)
def remove_expired_auth_tokens() -> int:
    with worker_session() as session:
        result = cast(
            CursorResult[Any],
            session.execute(delete(AuthToken).where(AuthToken.expires_at < datetime.now(UTC))),
        )
        session.commit()
        return int(result.rowcount or 0)
