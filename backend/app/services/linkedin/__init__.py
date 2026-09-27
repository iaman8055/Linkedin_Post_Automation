"""LinkedIn integration boundary."""

from app.services.linkedin.client import LinkedInClient
from app.services.linkedin.service import LinkedInService

__all__ = ["LinkedInClient", "LinkedInService"]

