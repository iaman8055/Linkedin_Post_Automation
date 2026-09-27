from typing import Any

import httpx
from pytest import MonkeyPatch

from app.services.linkedin.client import LinkedInClient


def test_linkedin_client_uses_documented_oauth_requests(monkeypatch: MonkeyPatch) -> None:
    captured_form: dict[str, str] = {}

    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        if url == "https://www.linkedin.com/oauth/v2/accessToken":
            captured_form.update(kwargs["data"])
            return httpx.Response(
                200,
                json={
                    "access_token": "access-token",
                    "expires_in": 5_184_000,
                    "scope": "openid profile email w_member_social",
                },
                request=httpx.Request("POST", url),
            )
        assert url == "https://api.linkedin.com/rest/posts"
        assert kwargs["headers"]["Linkedin-Version"] == "202609"
        assert kwargs["headers"]["X-Restli-Protocol-Version"] == "2.0.0"
        assert kwargs["json"]["author"] == "urn:li:person:member-id"
        assert kwargs["json"]["lifecycleState"] == "PUBLISHED"
        return httpx.Response(
            201,
            headers={"x-restli-id": "urn:li:share:987654"},
            request=httpx.Request("POST", url),
        )

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        assert url == "https://api.linkedin.com/v2/userinfo"
        assert kwargs["headers"]["Authorization"] == "Bearer access-token"
        return httpx.Response(
            200,
            json={
                "sub": "member-id",
                "name": "Member Name",
                "picture": "https://example.com/profile.jpg",
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(httpx, "get", fake_get)
    client = LinkedInClient()

    token = client.exchange_code(
        code="code",
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="https://example.com/callback",
    )
    profile = client.get_user_info(token.access_token)
    post_id = client.create_text_post(
        access_token=token.access_token,
        member_id=profile.subject,
        commentary="Contract test",
        api_version="202609",
    )

    assert captured_form == {
        "grant_type": "authorization_code",
        "code": "code",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "redirect_uri": "https://example.com/callback",
    }
    assert token.expires_in == 5_184_000
    assert token.refresh_token is None
    assert profile.subject == "member-id"
    assert profile.email is None
    assert post_id == "urn:li:share:987654"
