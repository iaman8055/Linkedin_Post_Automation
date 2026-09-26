from datetime import UTC, datetime

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models import Base, Campaign, Post, User
from app.models.enums import ApprovalMode, CampaignStatus, PostStatus


def test_initial_schema_registers_expected_tables() -> None:
    expected_tables = {
        "ai_jobs",
        "audit_logs",
        "campaigns",
        "content_ideas",
        "hashtags",
        "linkedin_accounts",
        "notifications",
        "post_analytics",
        "post_hashtags",
        "post_media",
        "post_research_sources",
        "posts",
        "publishing_logs",
        "research_sources",
        "schedules",
        "templates",
        "user_settings",
        "users",
        "writing_profiles",
    }

    assert expected_tables == set(Base.metadata.tables)


def test_user_campaign_and_post_relationships(db_session: Session) -> None:
    user = User(email="author@example.com", password_hash="hashed", display_name="Author")
    campaign = Campaign(
        user=user,
        name="AI Week",
        topic="Artificial Intelligence",
        status=CampaignStatus.DRAFT,
        approval_mode=ApprovalMode.MANUAL,
    )
    post = Post(user=user, campaign=campaign, content="A useful first draft.")

    db_session.add(user)
    db_session.commit()

    assert post.id is not None
    assert post.status is PostStatus.DRAFT
    assert campaign.posts == [post]
    assert inspect(post).persistent
    assert post.created_at.tzinfo is not None or isinstance(post.created_at, datetime)
    assert post.created_at.replace(tzinfo=UTC).utcoffset() == UTC.utcoffset(None)

