from dataclasses import dataclass

from pydantic import BaseModel

from app.services.ai.tools.contracts import ToolRisk
from app.services.ai.tools.schemas import (
    CalendarArguments,
    CreateDraftArguments,
    EmptyArguments,
    LimitedArguments,
    RecentPostsArguments,
)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    risk: ToolRisk
    arguments_model: type[BaseModel]
    confirmation_summary: str | None = None


TOOL_DEFINITIONS = {
    item.name: item for item in (
        ToolDefinition(
            "get_recent_posts", "Read recent posts in the active workspace.",
            ToolRisk.READ, RecentPostsArguments,
        ),
        ToolDefinition(
            "get_top_posts", "Read top measured posts in the active workspace.",
            ToolRisk.READ, LimitedArguments,
        ),
        ToolDefinition(
            "get_writing_profile", "Read the active workspace writing profile.",
            ToolRisk.READ, EmptyArguments,
        ),
        ToolDefinition(
            "get_content_ideas", "Read saved ideas in the active workspace.",
            ToolRisk.READ, LimitedArguments,
        ),
        ToolDefinition(
            "get_content_plans", "Read content plans in the active workspace.",
            ToolRisk.READ, LimitedArguments,
        ),
        ToolDefinition(
            "get_knowledge", "Read explicitly enabled knowledge in the active workspace.",
            ToolRisk.READ, LimitedArguments,
        ),
        ToolDefinition(
            "get_calendar", "Read scheduled content in a bounded date range.",
            ToolRisk.READ, CalendarArguments,
        ),
        ToolDefinition(
            "create_draft", "Create a reviewable post draft in the active workspace.",
            ToolRisk.WRITE, CreateDraftArguments,
            "Create this post as a draft. It will not be scheduled or published.",
        ),
    )
}


def public_tool_definitions() -> list[dict[str, object]]:
    return [
        {
            "name": item.name,
            "description": item.description,
            "risk": item.risk.value,
            "input_schema": item.arguments_model.model_json_schema(),
        }
        for item in TOOL_DEFINITIONS.values()
    ]
