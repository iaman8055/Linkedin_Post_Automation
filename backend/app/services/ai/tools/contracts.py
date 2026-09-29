from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolRisk(StrEnum):
    READ = "read"
    WRITE = "write"


class CopilotToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolConfirmation(BaseModel):
    tool_name: str
    summary: str
    arguments: dict[str, Any]


class CopilotToolResult(BaseModel):
    status: Literal["completed", "confirmation_required"]
    tool_name: str
    risk: ToolRisk
    workspace_id: str
    output: dict[str, Any] | list[dict[str, Any]] | None = None
    confirmation: ToolConfirmation | None = None
