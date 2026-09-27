from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class AIMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIMessage(BaseModel):
    role: AIMessageRole
    content: str = Field(min_length=1)


class AIGenerationRequest(BaseModel):
    messages: list[AIMessage] = Field(min_length=1)
    model: str
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_output_tokens: int = Field(gt=0, le=100_000)
    response_schema: dict[str, Any] | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AIUsage(BaseModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class AIGenerationResult(BaseModel):
    text: str
    provider: str
    model: str
    provider_request_id: str | None = None
    finish_reason: str | None = None
    usage: AIUsage = Field(default_factory=AIUsage)
    structured_output: dict[str, Any] | list[Any] | None = None


class AIProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class AIProvider(Protocol):
    @property
    def name(self) -> str: ...

    def generate(self, request: AIGenerationRequest) -> AIGenerationResult: ...
