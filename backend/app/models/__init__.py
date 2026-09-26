"""SQLAlchemy model registry.

Importing this package registers all tables on ``Base.metadata`` for migrations.
"""

from app.models.ai_job import AIJob
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.campaign import Campaign
from app.models.content_idea import ContentIdea
from app.models.hashtag import Hashtag, PostHashtag
from app.models.linkedin_account import LinkedInAccount
from app.models.notification import Notification
from app.models.post import Post
from app.models.post_analytics import PostAnalytics
from app.models.post_media import PostMedia
from app.models.publishing_log import PublishingLog
from app.models.research_source import PostResearchSource, ResearchSource
from app.models.schedule import Schedule
from app.models.template import Template
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.writing_profile import WritingProfile

__all__ = [
    "AIJob",
    "AuditLog",
    "Base",
    "Campaign",
    "ContentIdea",
    "Hashtag",
    "LinkedInAccount",
    "Notification",
    "Post",
    "PostAnalytics",
    "PostHashtag",
    "PostMedia",
    "PostResearchSource",
    "PublishingLog",
    "ResearchSource",
    "Schedule",
    "Template",
    "User",
    "UserSettings",
    "WritingProfile",
]
