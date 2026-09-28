from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.content_idea import ContentIdea
from app.models.enums import IdeaStatus, PostStatus, TemplateStatus
from app.models.knowledge_item import KnowledgeItem
from app.models.post import Post
from app.models.template import Template
from app.models.user import User
from app.schemas.search import GlobalSearchFilters
from app.services.search import GlobalSearchService


def test_global_search_is_owner_scoped_and_searches_multiple_content_types(
    db_session: Session,
) -> None:
    owner = User(email="search@example.com", password_hash="hashed", display_name="Search")
    other = User(email="hidden@example.com", password_hash="hashed", display_name="Hidden")
    db_session.add_all([owner, other])
    db_session.flush()
    db_session.add_all([
        Post(
            user_id=owner.id, title="AI agents", content="A practical agent workflow",
            status=PostStatus.DRAFT,
        ),
        Post(user_id=other.id, title="AI agents hidden", content="Private other user post"),
        ContentIdea(
            user_id=owner.id, title="Agent reliability", topic="AI", category="technical",
            angle="Failure modes", description="Explain reliable AI agents",
            suggested_hook="Why agents fail", suggested_format="short", status=IdeaStatus.NEW,
        ),
        KnowledgeItem(
            user_id=owner.id, category="project", title="Agent project",
            content="Built a reliable AI agent", tags=["AI", "Python"], is_private=True,
        ),
        Template(
            user_id=owner.id, name="AI lesson", body="A reusable AI structure",
            placeholders=[], settings={}, status=TemplateStatus.ACTIVE,
        ),
    ])
    db_session.commit()

    result = GlobalSearchService(db_session).search(
        owner.id, GlobalSearchFilters(query="AI")
    )

    assert {item.entity_type for item in result.items} == {
        "post", "idea", "knowledge", "template"
    }
    assert all("hidden" not in item.title for item in result.items)


def test_global_search_applies_post_status_dates_and_knowledge_tags(
    db_session: Session,
) -> None:
    owner = User(email="filters@example.com", password_hash="hashed", display_name="Filters")
    db_session.add(owner)
    db_session.flush()
    post = Post(
        user_id=owner.id, title="Scheduled launch", content="Launch content",
        status=PostStatus.SCHEDULED,
    )
    post.created_at = datetime.now(UTC) - timedelta(days=2)
    knowledge = KnowledgeItem(
        user_id=owner.id, category="skill", title="Python", content="Async Python",
        tags=["backend"], is_private=True,
    )
    db_session.add_all([post, knowledge])
    db_session.commit()
    service = GlobalSearchService(db_session)

    posts = service.search(owner.id, GlobalSearchFilters(
        entity_type="post", status="SCHEDULED",
        date_from=(datetime.now(UTC) - timedelta(days=3)).date(),
    ))
    tagged = service.search(owner.id, GlobalSearchFilters(
        entity_type="knowledge", tag="backend"
    ))

    assert [item.title for item in posts.items] == ["Scheduled launch"]
    assert [item.title for item in tagged.items] == ["Python"]
