import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.audit_log import AuditLog
from app.models.enums import PostStatus
from app.models.post import Post
from app.models.post_analytics import PostAnalytics
from app.models.schedule import Schedule
from app.repositories.content_idea import ContentIdeaRepository
from app.repositories.content_plan import ContentPlanRepository
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.repositories.post import PostRepository
from app.repositories.post_analytics import PostAnalyticsRepository
from app.repositories.writing_profile import WritingProfileRepository
from app.schemas.post import PostCreate
from app.services.ai.tools.contracts import (
    CopilotToolCall,
    CopilotToolResult,
    ToolConfirmation,
    ToolRisk,
)
from app.services.ai.tools.registry import TOOL_DEFINITIONS
from app.services.ai.tools.schemas import (
    CalendarArguments,
    CreateDraftArguments,
    LimitedArguments,
    RecentPostsArguments,
)
from app.services.posts import PostService

logger = logging.getLogger(__name__)


class CopilotToolService:
    """Executes a fixed tool allowlist; model output never receives database access."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.posts = PostRepository(session)
        self.analytics = PostAnalyticsRepository(session)
        self.ideas = ContentIdeaRepository(session)
        self.plans = ContentPlanRepository(session)
        self.knowledge = KnowledgeItemRepository(session)
        self.profiles = WritingProfileRepository(session)

    def execute(
        self, user_id: UUID, call: CopilotToolCall, *, confirmed: bool = False
    ) -> CopilotToolResult:
        definition = TOOL_DEFINITIONS.get(call.name)
        if definition is None:
            raise ApplicationError(
                "COPILOT_TOOL_NOT_ALLOWED", "This AI action is not allowed.", 403
            )
        try:
            arguments = definition.arguments_model.model_validate(call.arguments)
        except ValidationError as exc:
            raise ApplicationError(
                "COPILOT_TOOL_INPUT_INVALID", "The AI action contained invalid input.", 422
            ) from exc
        workspace_id = self.posts.active_workspace_id(user_id)
        if definition.risk is ToolRisk.WRITE and not confirmed:
            result = CopilotToolResult(
                status="confirmation_required", tool_name=definition.name,
                risk=definition.risk, workspace_id=str(workspace_id),
                confirmation=ToolConfirmation(
                    tool_name=definition.name,
                    summary=definition.confirmation_summary or "Confirm this change.",
                    arguments=arguments.model_dump(mode="json"),
                ),
            )
            self._audit(user_id, workspace_id, definition.name, "confirmation_required")
            return result
        handler = getattr(self, f"_{definition.name}", None)
        if handler is None:
            raise ApplicationError(
                "COPILOT_TOOL_UNAVAILABLE", "This AI action is unavailable.", 503
            )
        output: dict[str, Any] | list[dict[str, Any]] = handler(user_id, arguments)
        self._audit(user_id, workspace_id, definition.name, "completed")
        logger.info(
            "copilot_tool_executed",
            extra={"user_id": str(user_id), "workspace_id": str(workspace_id),
                   "tool_name": definition.name, "tool_risk": definition.risk.value},
        )
        return CopilotToolResult(
            status="completed", tool_name=definition.name, risk=definition.risk,
            workspace_id=str(workspace_id), output=output,
        )

    def _get_recent_posts(
        self, user_id: UUID, arguments: RecentPostsArguments
    ) -> list[dict[str, Any]]:
        posts, _ = self.posts.list_filtered_for_user(
            user_id, status=arguments.status, limit=arguments.limit, offset=0
        )
        return [self._post(item) for item in posts]

    def _get_top_posts(
        self, user_id: UUID, arguments: LimitedArguments
    ) -> list[dict[str, Any]]:
        posts, _ = self.posts.list_filtered_for_user(
            user_id, status=PostStatus.PUBLISHED, limit=100, offset=0
        )
        by_id = {post.id: post for post in posts}
        measured = [
            item for item in self.analytics.latest_for_user(user_id)
            if item.post_id in by_id
        ]
        measured.sort(key=lambda item: item.engagement_rate or -1, reverse=True)
        return [
            {**self._post(by_id[item.post_id]), "analytics": self._analytics(item)}
            for item in measured[:arguments.limit]
        ]

    def _get_writing_profile(
        self, user_id: UUID, _arguments: BaseModel
    ) -> dict[str, Any]:
        profiles, _ = self.profiles.list_with_total(user_id)
        if not profiles:
            return {"available": False}
        profile = next((item for item in profiles if item.is_default), profiles[0])
        return {
            "available": True, "id": str(profile.id), "name": profile.name,
            "tone": profile.tone, "sentence_style": profile.sentence_style,
            "language": profile.language, "emoji_preference": profile.emoji_preference,
            "paragraph_length": profile.paragraph_length,
            "technical_depth": profile.technical_depth,
            "cta_preference": profile.cta_preference,
            "preferred_vocabulary": profile.preferred_vocabulary,
        }

    def _get_content_ideas(
        self, user_id: UUID, arguments: LimitedArguments
    ) -> list[dict[str, Any]]:
        ideas, _ = self.ideas.list_recent(user_id, limit=arguments.limit)
        return [{
            "id": str(item.id), "title": item.title, "topic": item.topic,
            "category": item.category, "angle": item.angle,
            "description": item.description, "status": item.status.value,
        } for item in ideas]

    def _get_content_plans(
        self, user_id: UUID, arguments: LimitedArguments
    ) -> list[dict[str, Any]]:
        return [{
            "id": str(item.id), "name": item.name, "audience": item.audience,
            "timezone": item.timezone, "status": item.status.value,
            "item_count": len(item.items),
        } for item in self.plans.list_with_items(user_id)[:arguments.limit]]

    def _get_knowledge(
        self, user_id: UUID, arguments: LimitedArguments
    ) -> list[dict[str, Any]]:
        items, _ = self.knowledge.list_with_total(user_id)
        return [{
            "id": str(item.id), "category": item.category, "title": item.title,
            "content": item.content, "tags": item.tags,
        } for item in items[:arguments.limit]]

    def _get_calendar(
        self, user_id: UUID, arguments: CalendarArguments
    ) -> list[dict[str, Any]]:
        if arguments.end <= arguments.start:
            raise ApplicationError(
                "COPILOT_TOOL_INPUT_INVALID", "Calendar end must be after start.", 422
            )
        workspace_id = self.posts.active_workspace_id(user_id)
        schedules = self.session.scalars(
            select(Schedule).join(Post, Post.id == Schedule.post_id).where(
                Schedule.user_id == user_id,
                Post.workspace_id == workspace_id,
                Schedule.scheduled_for >= arguments.start,
                Schedule.scheduled_for < arguments.end,
            ).order_by(Schedule.scheduled_for).limit(100)
        )
        return [{
            "schedule_id": str(item.id), "post_id": str(item.post_id),
            "title": item.post.title, "status": item.status.value,
            "scheduled_for": item.scheduled_for.isoformat(), "timezone": item.timezone,
        } for item in schedules]

    def _create_draft(
        self, user_id: UUID, arguments: CreateDraftArguments
    ) -> dict[str, Any]:
        post = PostService(self.session).create(user_id, PostCreate(**arguments.model_dump()))
        return self._post(post)

    def _audit(self, user_id: UUID, workspace_id: UUID, tool_name: str, outcome: str) -> None:
        self.session.add(AuditLog(
            user_id=user_id, action="copilot_tool", resource_type="ai_tool",
            details={"workspace_id": str(workspace_id), "tool_name": tool_name,
                     "outcome": outcome},
        ))
        self.session.commit()

    @staticmethod
    def _post(item: Post) -> dict[str, Any]:
        return {
            "id": str(item.id), "title": item.title, "content": item.content,
            "status": item.status.value, "language": item.language,
            "created_at": item.created_at.isoformat(),
            "published_at": item.published_at.isoformat() if item.published_at else None,
        }

    @staticmethod
    def _analytics(item: PostAnalytics) -> dict[str, Any]:
        return {
            "impressions": item.impressions, "reactions": item.likes,
            "comments": item.comments, "reposts": item.shares,
            "engagement_rate": item.engagement_rate,
            "captured_at": item.captured_at.isoformat(),
        }
