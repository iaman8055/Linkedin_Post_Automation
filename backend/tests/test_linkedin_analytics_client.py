import httpx
import pytest

from app.services.linkedin.client import LinkedInClient, LinkedInClientError


def test_linkedin_client_reads_single_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        captured.update(kwargs)
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={"elements": [{"metricType": "IMPRESSION", "count": 420}]},
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    count = LinkedInClient().get_member_post_metric(
        access_token="token",
        post_urn="urn:li:share:123",
        metric="IMPRESSION",
        api_version="202609",
    )
    assert count == 420
    assert captured["params"] == {
        "q": "entity",
        "entity": "(share:urn:li:share:123)",
        "queryType": "IMPRESSION",
        "aggregation": "TOTAL",
    }


def test_linkedin_client_preserves_permission_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(403, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    with pytest.raises(LinkedInClientError) as error:
        LinkedInClient().get_member_post_metric(
            access_token="token",
            post_urn="urn:li:share:123",
            metric="COMMENT",
            api_version="202609",
        )
    assert error.value.status_code == 403
