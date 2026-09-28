from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_job import AIJob
from app.models.creator_progress import Achievement, CreatorGoal
from app.models.enums import AIJobStatus, PostStatus
from app.models.post import Post
from app.repositories.post_analytics import PostAnalyticsRepository
from app.schemas.creator_progress import AchievementResponse, CreatorProgressResponse


class CreatorProgressService:
    achievement_catalog = {
        "FIRST_POST": ("First post", "Published your first LinkedIn post."),
        "TEN_POSTS": ("10 posts", "Published 10 LinkedIn posts."),
        "FIFTY_POSTS": ("50 posts", "Published 50 LinkedIn posts."),
        "SEVEN_DAY_STREAK": ("7-day streak", "Published on seven consecutive days."),
        "THIRTY_DAY_STREAK": ("30-day streak", "Published on 30 consecutive days."),
        "TEN_K_IMPRESSIONS": ("10K impressions", "Reached 10,000 measured impressions."),
    }

    def __init__(self, session: Session) -> None:
        self.session = session
        self.analytics = PostAnalyticsRepository(session)

    def get(self, user_id: UUID) -> CreatorProgressResponse:
        published_values = list(self.session.scalars(
            select(Post.published_at).where(
                Post.user_id == user_id, Post.status == PostStatus.PUBLISHED,
                Post.published_at.is_not(None),
            ).order_by(Post.published_at.desc())
        ))
        published_dates = [value for value in published_values if value is not None]
        posts_published = len(published_dates)
        drafts_created = int(self.session.scalar(
            select(func.count()).select_from(Post).where(
                Post.user_id == user_id, Post.status == PostStatus.DRAFT
            )
        ) or 0)
        ideas_generated = int(self.session.scalar(
            select(func.count()).select_from(AIJob).where(
                AIJob.user_id == user_id,
                AIJob.job_type == "generate_content_ideas",
                AIJob.status == AIJobStatus.SUCCEEDED,
            )
        ) or 0)
        latest = self.analytics.latest_for_user(user_id)
        impression_values = [item.impressions for item in latest if item.impressions is not None]
        total_impressions = sum(impression_values) if impression_values else None
        streak = self._streak(published_dates)
        now = datetime.now(UTC)
        month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        monthly_posts = len([
            value for value in published_dates if self._as_utc(value) >= month_start
        ])
        goal = self.session.scalar(select(CreatorGoal).where(CreatorGoal.user_id == user_id))
        if goal is None:
            goal = CreatorGoal(user_id=user_id, monthly_post_target=8)
            self.session.add(goal)
            self.session.flush()
        self._unlock(user_id, posts_published, streak, total_impressions)
        self.session.commit()
        points = posts_published * 100 + drafts_created * 20 + ideas_generated * 10
        achievements = list(self.session.scalars(
            select(Achievement).where(Achievement.user_id == user_id)
            .order_by(Achievement.unlocked_at.desc())
        ))
        return CreatorProgressResponse(
            creator_level=1 + points // 500, level_points=points % 500,
            next_level_points=500, posts_published=posts_published,
            drafts_created=drafts_created, ideas_generated=ideas_generated,
            total_impressions=total_impressions, current_streak=streak,
            monthly_post_target=goal.monthly_post_target,
            monthly_posts_published=monthly_posts,
            monthly_goal_percent=min(100, round(monthly_posts / goal.monthly_post_target * 100)),
            achievements=[AchievementResponse(
                code=item.code, title=self.achievement_catalog[item.code][0],
                description=self.achievement_catalog[item.code][1], unlocked_at=item.unlocked_at,
            ) for item in achievements],
        )

    def update_goal(self, user_id: UUID, target: int) -> CreatorProgressResponse:
        goal = self.session.scalar(select(CreatorGoal).where(CreatorGoal.user_id == user_id))
        if goal is None:
            self.session.add(CreatorGoal(user_id=user_id, monthly_post_target=target))
        else:
            goal.monthly_post_target = target
        self.session.commit()
        return self.get(user_id)

    def _unlock(
        self, user_id: UUID, posts: int, streak: int, impressions: int | None
    ) -> None:
        eligible = set()
        if posts >= 1:
            eligible.add("FIRST_POST")
        if posts >= 10:
            eligible.add("TEN_POSTS")
        if posts >= 50:
            eligible.add("FIFTY_POSTS")
        if streak >= 7:
            eligible.add("SEVEN_DAY_STREAK")
        if streak >= 30:
            eligible.add("THIRTY_DAY_STREAK")
        if impressions is not None and impressions >= 10_000:
            eligible.add("TEN_K_IMPRESSIONS")
        existing = set(self.session.scalars(
            select(Achievement.code).where(Achievement.user_id == user_id)
        ))
        now = datetime.now(UTC)
        self.session.add_all([
            Achievement(user_id=user_id, code=code, unlocked_at=now)
            for code in eligible - existing
        ])

    @staticmethod
    def _streak(values: list[datetime]) -> int:
        days = sorted(
            {CreatorProgressService._as_utc(value).date() for value in values},
            reverse=True,
        )
        if not days:
            return 0
        today = datetime.now(UTC).date()
        if days[0] not in {today, today - timedelta(days=1)}:
            return 0
        streak = 1
        for previous, current in zip(days, days[1:], strict=False):
            if previous - current != timedelta(days=1):
                break
            streak += 1
        return streak

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
