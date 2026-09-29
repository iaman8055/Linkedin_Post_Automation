from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CopilotEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=500)
    post_id: UUID | None = None


class ProposedCopilotAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: Literal["create_draft"]
    arguments: dict[str, Any]


class GeneratedCopilotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1, max_length=6000)
    evidence: list[CopilotEvidence] = Field(default_factory=list, max_length=10)
    suggested_action: str | None = Field(default=None, max_length=300)
    proposed_action: ProposedCopilotAction | None = None


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=160)


class SendCopilotMessageRequest(BaseModel):
    content: str = Field(min_length=2, max_length=4000)
    use_writing_style: bool = True
    use_analytics: bool = True
    use_knowledge: bool = False


class CopilotActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tool_name: str
    arguments: dict[str, Any]
    status: str
    expires_at: datetime
    result: dict[str, Any] | list[dict[str, Any]] | None


class CopilotMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    evidence: list[CopilotEvidence]
    suggested_action: str | None
    created_at: datetime
    action: CopilotActionResponse | None = None


class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    last_message_at: datetime | None
    created_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationSummaryResponse]


class ConversationResponse(ConversationSummaryResponse):
    messages: list[CopilotMessageResponse]


class SendCopilotMessageResponse(BaseModel):
    conversation: ConversationResponse
    assistant_message: CopilotMessageResponse
