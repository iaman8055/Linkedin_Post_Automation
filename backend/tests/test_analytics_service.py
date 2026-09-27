from datetime import UTC, datetime

from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import PostStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.post import Post
from app.models.post_analytics import PostAnalytics
from app.models.user import User
from app.services.analytics import AnalyticsService
from app.services.linkedin.token_cipher import TokenCipher


class AnalyticsClient:
    values = {"IMPRESSION": 1000, "REACTION": 80, "COMMENT": 15, "RESHARE": 5}

    def get_member_post_metric(self, **kwargs: str) -> int:
        return self.values[kwargs["metric"]]


def test_analytics_collection_uses_only_linkedin_metrics(db_session: Session) -> None:
    key = Fernet.generate_key().decode()
    settings = Settings(linkedin_token_encryption_key=SecretStr(key))
    user = User(email="analytics@example.com", password_hash="hashed", display_name="Analyst")
    post = Post(
        user=user,
        title="Published insight",
        content="Measured post",
        status=PostStatus.PUBLISHED,
        linkedin_post_id="urn:li:share:123",
        published_at=datetime.now(UTC),
    )
    account = LinkedInAccount(
        user=user,
        linkedin_member_id="member-1",
        encrypted_access_token=TokenCipher(key).encrypt("access-token"),
        scopes="openid w_member_social r_member_postAnalytics",
        is_connected=True,
    )
    db_session.add_all([user, post, account])
    db_session.commit()

    service = AnalyticsService(db_session, settings, AnalyticsClient())  # type: ignore[arg-type]
    snapshot = service.collect(user.id, post.id)
    assert snapshot.impressions == 1000
    assert snapshot.likes == 80
    assert snapshot.comments == 15
    assert snapshot.shares == 5
    assert snapshot.engagement_rate == 10.0
    overview = service.overview(user.id)
    assert overview.total_impressions == 1000
    assert overview.posts[0].post_id == post.id


def test_performance_insights_require_enough_user_data(db_session: Session) -> None:
    user = User(email="few-insights@example.com", password_hash="hashed", display_name="Few")
    post = Post(user=user, content="Only one measured post", status=PostStatus.PUBLISHED)
    db_session.add_all([user, post])
    db_session.flush()
    snapshot = PostAnalytics(
        user_id=user.id, post=post, impressions=100, likes=5, comments=1, shares=0,
        engagement_rate=6.0, captured_at=datetime.now(UTC),
    )
    db_session.add(snapshot)
    db_session.commit()

    service = AnalyticsService(db_session, Settings(), AnalyticsClient())  # type: ignore[arg-type]
    result = service.performance_insights(user.id)
    assert result.status == "insufficient_data"
    assert result.analyzed_posts == 1
    assert result.minimum_required == 5
    assert result.insights == []


def test_performance_insights_use_latest_owned_snapshots(db_session: Session) -> None:
    user = User(email="insights@example.com", password_hash="hashed", display_name="Insights")
    posts = [
        Post(
            user=user, title=f"Post {index}",
            content="Short content" if index < 3 else "M" * 700,
            status=PostStatus.PUBLISHED,
            published_at=datetime(2026, 9, 21 + index, 9, tzinfo=UTC),
        )
        for index in range(5)
    ]
    db_session.add_all([user, *posts])
    db_session.flush()
    snapshots = [
        PostAnalytics(
            user_id=user.id, post=post, impressions=100, likes=index + 1, comments=0, shares=0,
            engagement_rate=float(index + 1), captured_at=datetime.now(UTC),
        )
        for index, post in enumerate(posts)
    ]
    db_session.add_all(snapshots)
    db_session.commit()

    service = AnalyticsService(db_session, Settings(), AnalyticsClient())  # type: ignore[arg-type]
    result = service.performance_insights(user.id)
    assert result.status == "ready"
    assert result.analyzed_posts == 5
    assert result.insights[0].type == "top_post"
    assert "Post 4" in result.insights[0].observation
    assert any(item.type == "content_length" for item in result.insights)
