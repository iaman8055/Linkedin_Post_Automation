from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from pydantic import ValidationError

from app.services.research.contracts import (
    ResearchProviderError,
    ResearchQuery,
    ResearchResponse,
    ResearchResult,
)


class TavilyResearchProvider:
    name = "tavily"

    def __init__(self, api_key: str, base_url: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search(self, query: ResearchQuery) -> ResearchResponse:
        try:
            response = httpx.post(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query.query,
                    "topic": query.topic,
                    "search_depth": "basic",
                    "max_results": query.max_results,
                    "time_range": query.time_range,
                    "include_answer": "basic",
                    "include_published_date": True,
                    "include_raw_content": False,
                    "safe_search": True,
                },
                timeout=self.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ResearchProviderError(
                "RESEARCH_TIMEOUT", "The research provider timed out.", retryable=True
            ) from exc
        except httpx.HTTPError as exc:
            raise ResearchProviderError(
                "RESEARCH_UNAVAILABLE", "The research provider is unavailable.", retryable=True
            ) from exc
        if response.status_code == 429:
            raise ResearchProviderError(
                "RESEARCH_RATE_LIMITED",
                "The research provider rate limit was reached.",
                retryable=True,
            )
        if response.status_code in {432, 433}:
            raise ResearchProviderError(
                "RESEARCH_USAGE_LIMIT", "The research provider usage limit was reached."
            )
        if response.status_code in {401, 403}:
            raise ResearchProviderError(
                "RESEARCH_AUTH_FAILED", "The research provider credentials were rejected."
            )
        if response.status_code >= 500:
            raise ResearchProviderError(
                "RESEARCH_UNAVAILABLE", "The research provider is unavailable.", retryable=True
            )
        if response.status_code >= 400:
            raise ResearchProviderError(
                "RESEARCH_REQUEST_INVALID", "The research provider rejected the request."
            )
        try:
            data: dict[str, Any] = response.json()
            results = [
                ResearchResult(
                    title=item["title"],
                    url=item["url"],
                    content=item.get("content") or "",
                    score=item.get("score"),
                    published_at=self._published_at(item.get("published_date")),
                )
                for item in data.get("results", [])
            ]
            return ResearchResponse(
                answer=data.get("answer"),
                results=results,
                provider=self.name,
                request_id=data.get("request_id"),
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise ResearchProviderError(
                "RESEARCH_RESPONSE_INVALID", "The research provider returned invalid data."
            ) from exc

    @staticmethod
    def _published_at(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
