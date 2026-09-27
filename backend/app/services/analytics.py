from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApplicationError
from app.models.enums import PostStatus
from app.models.linkedin_account import LinkedInAccount
from app.models.post_analytics import PostAnalytics
from app.repositories.linkedin_account import LinkedInAccountRepository
from app.repositories.post_analytics import PostAnalyticsRepository
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsPostItem,
    PerformanceInsight,
    PerformanceInsightsResponse,
    PostAnalyticsResponse,
)
from app.services.linkedin.client import LinkedInClient, LinkedInClientError
from app.services.linkedin.scopes import parse_linkedin_scopes
from app.services.linkedin.token_cipher import TokenCipher, TokenCipherError
from app.services.posts import PostService


class AnalyticsService:
    minimum_insight_posts = 5
    required_scope = "r_member_postAnalytics"
    metrics = {
        "IMPRESSION": "impressions",
        "REACTION": "likes",
        "COMMENT": "comments",
        "RESHARE": "shares",
    }

    def __init__(
        self, session: Session, settings: Settings, client: LinkedInClient
    ) -> None:
        self.session = session
        self.settings = settings
        self.client = client
        self.accounts = LinkedInAccountRepository(session)
        self.analytics = PostAnalyticsRepository(session)

    def status(self, user_id: UUID) -> tuple[bool, bool]:
        account = self.accounts.get_connected_for_user(user_id)
        if account is None:
            return False, False
        return True, self.required_scope in self._scopes(account)

    def collect(self, user_id: UUID, post_id: UUID) -> PostAnalytics:
        post = PostService(self.session).get(user_id, post_id)
        if post.status != PostStatus.PUBLISHED or not post.linkedin_post_id:
            raise ApplicationError(
                "ANALYTICS_POST_NOT_PUBLISHED",
                "Analytics are available only for published LinkedIn posts.",
                409,
            )
        account = self._account(user_id)
        token = self._access_token(account)
        values: dict[str, int] = {}
        try:
            for metric, field in self.metrics.items():
                values[field] = self.client.get_member_post_metric(
                    access_token=token,
                    post_urn=post.linkedin_post_id,
                    metric=metric,
                    api_version=self.settings.linkedin_api_version,
                )
        except LinkedInClientError as exc:
            if exc.status_code in {401, 403}:
                raise ApplicationError(
                    "LINKEDIN_ANALYTICS_PERMISSION_DENIED",
                    "LinkedIn denied analytics access. Reconnect after enabling the "
                    "required product.",
                    403,
                ) from exc
            if exc.status_code == 429:
                raise ApplicationError(
                    "LINKEDIN_ANALYTICS_RATE_LIMITED", "LinkedIn rate limit reached.", 429
                ) from exc
            raise ApplicationError(
                "LINKEDIN_ANALYTICS_FAILED", "LinkedIn analytics could not be collected.", 502
            ) from exc
        impressions = values["impressions"]
        engagements = values["likes"] + values["comments"] + values["shares"]
        engagement_rate = (engagements / impressions * 100) if impressions > 0 else None
        snapshot = self.analytics.add(PostAnalytics(
            user_id=user_id,
            post_id=post.id,
            impressions=impressions,
            likes=values["likes"],
            comments=values["comments"],
            shares=values["shares"],
            engagement_rate=engagement_rate,
            captured_at=datetime.now(UTC),
            provider_payload={"provider": "linkedin", "metrics": list(self.metrics)},
        ))
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def overview(self, user_id: UUID) -> AnalyticsOverviewResponse:
        latest = self.analytics.latest_for_user(user_id)
        items = [AnalyticsPostItem(
            post_id=item.post_id,
            title=item.post.title,
            content_excerpt=item.post.content[:160],
            published_at=item.post.published_at,
            analytics=PostAnalyticsResponse.model_validate(item),
        ) for item in latest]
        rates = [item.engagement_rate for item in latest if item.engagement_rate is not None]
        return AnalyticsOverviewResponse(
            posts=items,
            total_impressions=self._sum(latest, "impressions"),
            total_likes=self._sum(latest, "likes"),
            total_comments=self._sum(latest, "comments"),
            total_shares=self._sum(latest, "shares"),
            average_engagement_rate=sum(rates) / len(rates) if rates else None,
        )

    def history(self, user_id: UUID, post_id: UUID) -> list[PostAnalytics]:
        PostService(self.session).get(user_id, post_id)
        return self.analytics.history_for_post(user_id, post_id, limit=100)

    def performance_insights(self, user_id: UUID) -> PerformanceInsightsResponse:
        latest = [
            item for item in self.analytics.latest_for_user(user_id)
            if item.engagement_rate is not None
        ]
        disclaimer = (
            "Observations are based only on your available LinkedIn analytics and are not "
            "universal LinkedIn rules."
        )
        if len(latest) < self.minimum_insight_posts:
            return PerformanceInsightsResponse(
                status="insufficient_data",
                analyzed_posts=len(latest),
                minimum_required=self.minimum_insight_posts,
                disclaimer=disclaimer,
                insights=[],
            )

        user_settings = latest[0].post.user.settings
        timezone_name = user_settings.timezone if user_settings else "UTC"
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            timezone_name = "UTC"
            timezone = ZoneInfo("UTC")

        insights = [self._top_post_insight(latest)]
        length_insight = self._length_insight(latest)
        if length_insight is not None:
            insights.append(length_insight)
        timing_insight = self._timing_insight(latest, timezone, timezone_name)
        if timing_insight is not None:
            insights.append(timing_insight)
        campaign_insight = self._campaign_insight(latest)
        if campaign_insight is not None:
            insights.append(campaign_insight)
        return PerformanceInsightsResponse(
            status="ready",
            analyzed_posts=len(latest),
            minimum_required=self.minimum_insight_posts,
            disclaimer=disclaimer,
            insights=insights,
        )

    @staticmethod
    def _top_post_insight(items: list[PostAnalytics]) -> PerformanceInsight:
        top = max(items, key=lambda item: item.engagement_rate or 0)
        label = top.post.title or top.post.content[:60].strip()
        return PerformanceInsight(
            type="top_post",
            title="Highest-engagement post",
            observation=f'“{label}” had the highest measured engagement rate.',
            evidence=f"{top.engagement_rate:.2f}% engagement from its latest snapshot.",
            sample_size=len(items),
        )

    @staticmethod
    def _length_insight(items: list[PostAnalytics]) -> PerformanceInsight | None:
        buckets: dict[str, list[float]] = defaultdict(list)
        for item in items:
            length = len(item.post.content)
            label = "Short (<500 characters)" if length < 500 else (
                "Medium (500–1,200 characters)" if length <= 1200 else "Long (>1,200 characters)"
            )
            buckets[label].append(item.engagement_rate or 0)
        eligible = {key: values for key, values in buckets.items() if len(values) >= 2}
        if len(eligible) < 2:
            return None
        label, values = max(eligible.items(), key=lambda item: sum(item[1]) / len(item[1]))
        average = sum(values) / len(values)
        return PerformanceInsight(
            type="content_length",
            title="Content-length pattern",
            observation=f"{label} performed best among length groups with enough samples.",
            evidence=f"Average engagement was {average:.2f}% across {len(values)} posts.",
            sample_size=len(values),
        )

    @staticmethod
    def _timing_insight(
        items: list[PostAnalytics], timezone: ZoneInfo, timezone_name: str
    ) -> PerformanceInsight | None:
        groups: dict[str, list[float]] = defaultdict(list)
        for item in items:
            if item.post.published_at is None:
                continue
            local = item.post.published_at.astimezone(timezone)
            period = "morning" if local.hour < 12 else "afternoon" if local.hour < 17 else "evening"
            groups[f"{local.strftime('%A')} {period}"].append(item.engagement_rate or 0)
        eligible = {key: values for key, values in groups.items() if len(values) >= 2}
        if not eligible:
            return None
        label, values = max(eligible.items(), key=lambda item: sum(item[1]) / len(item[1]))
        average = sum(values) / len(values)
        return PerformanceInsight(
            type="publishing_time",
            title="Publishing-time pattern",
            observation=f"{label} had the strongest average in your {timezone_name} timezone.",
            evidence=f"Average engagement was {average:.2f}% across {len(values)} posts.",
            sample_size=len(values),
        )

    @staticmethod
    def _campaign_insight(items: list[PostAnalytics]) -> PerformanceInsight | None:
        groups: dict[str, list[float]] = defaultdict(list)
        for item in items:
            if item.post.campaign is not None:
                groups[item.post.campaign.name].append(item.engagement_rate or 0)
        eligible = {key: values for key, values in groups.items() if len(values) >= 2}
        if len(eligible) < 2:
            return None
        label, values = max(eligible.items(), key=lambda item: sum(item[1]) / len(item[1]))
        average = sum(values) / len(values)
        return PerformanceInsight(
            type="campaign",
            title="Campaign pattern",
            observation=f'“{label}” had the strongest average among comparable campaigns.',
            evidence=f"Average engagement was {average:.2f}% across {len(values)} posts.",
            sample_size=len(values),
        )

    def _account(self, user_id: UUID) -> LinkedInAccount:
        account = self.accounts.get_connected_for_user(user_id)
        if account is None:
            raise ApplicationError("LINKEDIN_ACCOUNT_DISCONNECTED", "Reconnect LinkedIn.", 409)
        if account.token_expires_at is not None:
            expires_at = account.token_expires_at
            comparable = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=UTC)
            if comparable <= datetime.now(UTC):
                raise ApplicationError("LINKEDIN_TOKEN_EXPIRED", "Reconnect LinkedIn.", 409)
        if self.required_scope not in self._scopes(account):
            raise ApplicationError(
                "LINKEDIN_ANALYTICS_SCOPE_MISSING",
                "Analytics require the r_member_postAnalytics permission.",
                403,
            )
        return account

    def _access_token(self, account: LinkedInAccount) -> str:
        key = self.settings.linkedin_token_encryption_key
        if key is None:
            raise ApplicationError("LINKEDIN_NOT_CONFIGURED", "LinkedIn is not configured.", 503)
        try:
            return TokenCipher(key.get_secret_value()).decrypt(account.encrypted_access_token)
        except TokenCipherError as exc:
            raise ApplicationError(
                "LINKEDIN_TOKEN_UNAVAILABLE", "Reconnect LinkedIn.", 409
            ) from exc

    @staticmethod
    def _scopes(account: LinkedInAccount) -> set[str]:
        return parse_linkedin_scopes(account.scopes)

    @staticmethod
    def _sum(items: list[PostAnalytics], field: str) -> int | None:
        values = [getattr(item, field) for item in items if getattr(item, field) is not None]
        return sum(values) if values else None
