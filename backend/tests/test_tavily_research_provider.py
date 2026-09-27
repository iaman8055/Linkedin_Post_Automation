import httpx
import pytest

from app.services.research.contracts import ResearchProviderError, ResearchQuery
from app.services.research.tavily import TavilyResearchProvider


def test_tavily_search_maps_attributed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", "https://api.tavily.com/search")
        return httpx.Response(
            200,
            request=request,
            json={
                "answer": "A grounded summary.",
                "request_id": "request-1",
                "results": [{
                    "title": "Primary source",
                    "url": "https://example.com/report",
                    "content": "Relevant evidence.",
                    "score": 0.9,
                    "published_date": "2026-09-20T10:00:00Z",
                }],
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    result = TavilyResearchProvider("secret", "https://api.tavily.com", 30).search(
        ResearchQuery(query="AI agents")
    )
    assert result.answer == "A grounded summary."
    assert str(result.results[0].url) == "https://example.com/report"
    assert result.results[0].published_at is not None


def test_tavily_rate_limit_is_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            429, request=httpx.Request("POST", "https://api.tavily.com/search")
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    with pytest.raises(ResearchProviderError) as error:
        TavilyResearchProvider("secret", "https://api.tavily.com", 30).search(
            ResearchQuery(query="AI agents")
        )
    assert error.value.code == "RESEARCH_RATE_LIMITED"
    assert error.value.retryable is True
