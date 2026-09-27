from dataclasses import dataclass
from typing import Any, cast

import httpx


class LinkedInClientError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class LinkedInTokenResponse:
    access_token: str
    expires_in: int
    scope: str
    refresh_token: str | None = None
    refresh_token_expires_in: int | None = None


@dataclass(slots=True)
class LinkedInUserInfo:
    subject: str
    name: str | None
    picture: str | None
    email: str | None
    email_verified: bool | None


class LinkedInClient:
    authorization_endpoint = "https://www.linkedin.com/oauth/v2/authorization"
    token_endpoint = "https://www.linkedin.com/oauth/v2/accessToken"
    userinfo_endpoint = "https://api.linkedin.com/v2/userinfo"
    posts_endpoint = "https://api.linkedin.com/rest/posts"
    member_post_analytics_endpoint = (
        "https://api.linkedin.com/rest/memberCreatorPostAnalytics"
    )

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def exchange_code(
        self,
        *,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> LinkedInTokenResponse:
        try:
            response = httpx.post(
                self.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return LinkedInTokenResponse(
                access_token=str(payload["access_token"]),
                expires_in=int(payload["expires_in"]),
                scope=str(payload.get("scope", "")),
                refresh_token=(
                    str(payload["refresh_token"]) if payload.get("refresh_token") else None
                ),
                refresh_token_expires_in=(
                    int(payload["refresh_token_expires_in"])
                    if payload.get("refresh_token_expires_in") is not None
                    else None
                ),
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise LinkedInClientError("LinkedIn token exchange failed") from exc

    def get_user_info(self, access_token: str) -> LinkedInUserInfo:
        try:
            response = httpx.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return LinkedInUserInfo(
                subject=str(payload["sub"]),
                name=str(payload["name"]) if payload.get("name") else None,
                picture=str(payload["picture"]) if payload.get("picture") else None,
                email=str(payload["email"]) if payload.get("email") else None,
                email_verified=(
                    bool(payload["email_verified"])
                    if payload.get("email_verified") is not None
                    else None
                ),
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise LinkedInClientError("LinkedIn user information request failed") from exc

    def create_text_post(
        self,
        *,
        access_token: str,
        member_id: str,
        commentary: str,
        api_version: str,
    ) -> str:
        payload = {
            "author": f"urn:li:person:{member_id}",
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        try:
            response = httpx.post(
                self.posts_endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Linkedin-Version": api_version,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            if response.status_code != 201:
                raise LinkedInClientError(
                    "Unexpected LinkedIn post response", response.status_code
                )
            post_id = cast(str | None, response.headers.get("x-restli-id"))
            if not post_id:
                raise LinkedInClientError("LinkedIn post response did not include an ID", 502)
            return post_id
        except httpx.HTTPStatusError as exc:
            raise LinkedInClientError(
                "LinkedIn post creation failed", exc.response.status_code
            ) from exc
        except httpx.HTTPError as exc:
            raise LinkedInClientError("LinkedIn post creation failed") from exc

    def get_member_post_metric(
        self,
        *,
        access_token: str,
        post_urn: str,
        metric: str,
        api_version: str,
    ) -> int:
        entity_type = "ugc" if ":ugcPost:" in post_urn else "share"
        try:
            response = httpx.get(
                self.member_post_analytics_endpoint,
                params={
                    "q": "entity",
                    "entity": f"({entity_type}:{post_urn})",
                    "queryType": metric,
                    "aggregation": "TOTAL",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Linkedin-Version": api_version,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            elements = payload.get("elements") or []
            if not elements:
                return 0
            return int(elements[0]["count"])
        except httpx.HTTPStatusError as exc:
            raise LinkedInClientError(
                "LinkedIn analytics request failed", exc.response.status_code
            ) from exc
        except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError) as exc:
            raise LinkedInClientError("LinkedIn analytics response was invalid") from exc
