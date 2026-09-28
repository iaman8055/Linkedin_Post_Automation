from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.enums import PostStatus
from app.models.post import Post
from app.models.post_analytics import PostAnalytics
from app.models.user import User
from app.services.creator_progress import CreatorProgressService


def test_creator_progress_uses_real_activity_and_unlocks_achievements(
    db_session: Session,
) -> None:
    user = User(email="progress@example.com", password_hash="hashed", display_name="Creator")
    today = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0)
    posts = [
        Post(
            user=user, content=f"Published {index}", status=PostStatus.PUBLISHED,
            published_at=today - timedelta(days=index),
        )
        for index in range(2)
    ]
    draft = Post(user=user, content="Draft", status=PostStatus.DRAFT)
    db_session.add_all([user, *posts, draft])
    db_session.flush()
    db_session.add(PostAnalytics(
        user_id=user.id, post=posts[0], impressions=10_000, likes=50,
        comments=5, shares=2, engagement_rate=0.57, captured_at=today,
    ))
    db_session.commit()

    service = CreatorProgressService(db_session)
    result = service.get(user.id)

    assert result.posts_published == 2
    assert result.drafts_created == 1
    assert result.current_streak == 2
    assert result.total_impressions == 10_000
    assert {item.code for item in result.achievements} == {
        "FIRST_POST", "TEN_K_IMPRESSIONS"
    }
    updated = service.update_goal(user.id, 4)
    assert updated.monthly_post_target == 4
