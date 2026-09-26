"""Persistence repositories."""

from app.repositories.base import BaseRepository, UserOwnedRepository
from app.repositories.post import PostRepository

__all__ = ["BaseRepository", "PostRepository", "UserOwnedRepository"]

