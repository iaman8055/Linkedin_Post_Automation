import json
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus
from app.schemas.ai import AssistedPostContent, AssistPostRequest
from app.services.ai.contracts import AIGenerationRequest, AIMessage, AIMessageRole
from app.services.ai.execution import AIExecutionService
from app.services.ai.registry import AIProviderRegistry
from app.services.posts import PostService


class WritingAssistant:
    instructions = {
        "rewrite": "Rewrite the post while preserving its meaning and factual claims.",
        "shorten": "Make the post substantially shorter without losing its core value.",
        "expand": "Expand the post with useful explanation, without inventing facts.",
        "improve": "Improve clarity, flow, value, and engagement while keeping it authentic.",
        "change_tone": "Rewrite the post in the requested tone.",
        "improve_hook": "Replace the opening with a stronger hook and preserve the rest.",
        "improve_cta": "Improve or add a natural call to action at the end.",
        "add_hashtags": "Add a small set of relevant hashtags at the end.",
    }

    def __init__(
        self, session: Session, settings: Settings, registry: AIProviderRegistry
    ) -> None:
        self.session = session
        self.settings = settings
        self.execution = AIExecutionService(session, settings, registry)

    def assist(
        self, user_id: UUID, post_id: UUID, payload: AssistPostRequest
    ) -> tuple[UUID, str]:
        post = PostService(self.session).get(user_id, post_id)
        if post.status != PostStatus.DRAFT:
            raise ApplicationError(
                "POST_NOT_EDITABLE", "AI editing is available only for draft posts.", 409
            )
        if not self.settings.ai_model:
            raise ApplicationError("AI_MODEL_NOT_CONFIGURED", "AI model is not configured.", 503)
        if payload.action == "change_tone" and not payload.tone:
            raise ApplicationError("AI_TONE_REQUIRED", "Choose a tone for this action.", 422)

        input_data = {"content": post.content, "language": post.language}
        if payload.tone:
            input_data["requested_tone"] = payload.tone
        execution = self.execution.execute(
            user_id=user_id,
            job_type=f"assist_post_{payload.action}",
            request=AIGenerationRequest(
                model=self.settings.ai_model,
                max_output_tokens=self.settings.ai_max_output_tokens,
                response_schema=AssistedPostContent.model_json_schema(),
                metadata={"schema_name": "assisted_post"},
                messages=[
                    AIMessage(
                        role=AIMessageRole.SYSTEM,
                        content=(
                            "You are a LinkedIn writing assistant. Follow the requested edit only. "
                            "Never invent claims, quotations, statistics, or sources. Return only "
                            "the requested structured data."
                        ),
                    ),
                    AIMessage(
                        role=AIMessageRole.USER,
                        content=f"{self.instructions[payload.action]}\n{json.dumps(input_data)}",
                    ),
                ],
            ),
        )
        try:
            result = AssistedPostContent.model_validate(execution.result.structured_output)
        except ValidationError as exc:
            raise ApplicationError(
                "AI_OUTPUT_INVALID", "The AI provider returned invalid edited content.", 502
            ) from exc
        return execution.job.id, result.content.strip()
