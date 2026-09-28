from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.content_idea import ContentIdea
from app.models.enums import PostStatus
from app.models.knowledge_item import KnowledgeItem
from app.models.post import Post
from app.models.template import Template
from app.schemas.search import GlobalSearchFilters, GlobalSearchResponse, GlobalSearchResult


class GlobalSearchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(self, user_id: UUID, filters: GlobalSearchFilters) -> GlobalSearchResponse:
        items: list[GlobalSearchResult] = []
        kinds = {filters.entity_type} if filters.entity_type != "all" else {
            "post", "idea", "knowledge", "template"
        }
        if "post" in kinds:
            items.extend(self._posts(user_id, filters))
        if "idea" in kinds:
            items.extend(self._ideas(user_id, filters))
        if "knowledge" in kinds:
            items.extend(self._knowledge(user_id, filters))
        if "template" in kinds:
            items.extend(self._templates(user_id, filters))
        items.sort(key=lambda item: item.updated_at, reverse=True)
        total = len(items)
        return GlobalSearchResponse(
            items=items[:filters.limit], total=total,
            query=filters.query.strip() if filters.query else None,
        )

    def _posts(self, user_id: UUID, filters: GlobalSearchFilters) -> list[GlobalSearchResult]:
        conditions = [Post.user_id == user_id]
        self._dates(conditions, Post.created_at, filters)
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            conditions.append(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))
        if filters.status:
            try:
                conditions.append(Post.status == PostStatus(filters.status.upper()))
            except ValueError:
                return []
        posts = self.session.scalars(
            select(Post).where(*conditions).options(selectinload(Post.schedules))
            .order_by(Post.updated_at.desc()).limit(filters.limit)
        )
        results = []
        for post in posts:
            upcoming = [schedule.scheduled_for for schedule in post.schedules]
            results.append(GlobalSearchResult(
                id=post.id, entity_type="post", title=post.title or "Untitled post",
                excerpt=post.content[:240], status=post.status.value, topic=None, tags=[],
                updated_at=post.updated_at,
                scheduled_for=min(upcoming) if upcoming else None,
                url=f"/posts/{post.id}",
            ))
        return results

    def _ideas(self, user_id: UUID, filters: GlobalSearchFilters) -> list[GlobalSearchResult]:
        conditions = [ContentIdea.user_id == user_id]
        self._dates(conditions, ContentIdea.created_at, filters)
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            conditions.append(or_(
                ContentIdea.title.ilike(pattern), ContentIdea.description.ilike(pattern),
                ContentIdea.angle.ilike(pattern),
            ))
        if filters.topic:
            conditions.append(ContentIdea.topic.ilike(f"%{filters.topic.strip()}%"))
        ideas = self.session.scalars(
            select(ContentIdea).where(*conditions)
            .order_by(ContentIdea.updated_at.desc()).limit(filters.limit)
        )
        return [GlobalSearchResult(
            id=item.id, entity_type="idea", title=item.title,
            excerpt=item.description[:240], status=item.status.value, topic=item.topic,
            tags=[item.category], updated_at=item.updated_at, url="/studio",
        ) for item in ideas]

    def _knowledge(
        self, user_id: UUID, filters: GlobalSearchFilters
    ) -> list[GlobalSearchResult]:
        conditions = [KnowledgeItem.user_id == user_id]
        self._dates(conditions, KnowledgeItem.created_at, filters)
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            conditions.append(or_(
                KnowledgeItem.title.ilike(pattern), KnowledgeItem.content.ilike(pattern)
            ))
        records = list(self.session.scalars(
            select(KnowledgeItem).where(*conditions)
            .order_by(KnowledgeItem.updated_at.desc()).limit(filters.limit)
        ))
        if filters.tag:
            tag = filters.tag.strip().casefold()
            records = [
                item for item in records
                if any(value.casefold() == tag for value in item.tags)
            ]
        return [GlobalSearchResult(
            id=item.id, entity_type="knowledge", title=item.title,
            excerpt=item.content[:240], status="PRIVATE" if item.is_private else None,
            topic=item.category, tags=item.tags, updated_at=item.updated_at,
            url="/knowledge",
        ) for item in records]

    def _templates(
        self, user_id: UUID, filters: GlobalSearchFilters
    ) -> list[GlobalSearchResult]:
        conditions = [Template.user_id == user_id]
        self._dates(conditions, Template.created_at, filters)
        if filters.query:
            pattern = f"%{filters.query.strip()}%"
            conditions.append(or_(
                Template.name.ilike(pattern), Template.description.ilike(pattern),
                Template.body.ilike(pattern),
            ))
        templates = self.session.scalars(
            select(Template).where(*conditions)
            .order_by(Template.updated_at.desc()).limit(filters.limit)
        )
        return [GlobalSearchResult(
            id=item.id, entity_type="template", title=item.name,
            excerpt=(item.description or item.body)[:240], status=item.status.value,
            topic=None, tags=item.placeholders, updated_at=item.updated_at,
            url="/templates",
        ) for item in templates]

    @staticmethod
    def _dates(
        conditions: list[ColumnElement[bool]],
        column: InstrumentedAttribute[datetime],
        filters: GlobalSearchFilters,
    ) -> None:
        if filters.date_from:
            conditions.append(column >= datetime.combine(filters.date_from, time.min, UTC))
        if filters.date_to:
            conditions.append(
                column < datetime.combine(filters.date_to + timedelta(days=1), time.min, UTC)
            )
