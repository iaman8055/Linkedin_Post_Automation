from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field, HttpUrl


class ResearchQuery(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    topic: str = "general"
    max_results: int = Field(default=5, ge=1, le=10)
    time_range: str | None = None


class ResearchResult(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    content: str = Field(default="", max_length=10_000)
    score: float | None = None
    published_at: datetime | None = None


class ResearchResponse(BaseModel):
    answer: str | None = None
    results: list[ResearchResult]
    provider: str
    request_id: str | None = None


class ResearchProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ResearchProvider(Protocol):
    @property
    def name(self) -> str: ...

    def search(self, query: ResearchQuery) -> ResearchResponse: ...
