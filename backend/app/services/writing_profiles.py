import json
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.writing_profile import WritingProfile
from app.repositories.writing_profile import WritingProfileRepository
from app.schemas.writing_profile import WritingProfileCreate, WritingProfileUpdate


class WritingProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.profiles = WritingProfileRepository(session)

    def create(self, user_id: UUID, payload: WritingProfileCreate) -> WritingProfile:
        values = self._clean(payload.model_dump())
        self._validate_guidance(values["additional_guidance"])
        _, total = self.profiles.list_with_total(user_id)
        values["is_default"] = values["is_default"] or total == 0
        if values["is_default"]:
            self.profiles.clear_default(user_id)
        profile = self.profiles.create_for_user(user_id, **values)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def list_profiles(self, user_id: UUID) -> tuple[list[WritingProfile], int]:
        return self.profiles.list_with_total(user_id)

    def get(self, user_id: UUID, profile_id: UUID) -> WritingProfile:
        profile = self.profiles.get_for_user(profile_id, user_id)
        if profile is None:
            raise ApplicationError("WRITING_PROFILE_NOT_FOUND", "Writing profile not found.", 404)
        return profile

    def update(
        self, user_id: UUID, profile_id: UUID, payload: WritingProfileUpdate
    ) -> WritingProfile:
        profile = self.get(user_id, profile_id)
        values = self._clean(payload.model_dump(exclude_unset=True))
        if values.get("additional_guidance") is not None:
            self._validate_guidance(values["additional_guidance"])
        if values.get("is_default"):
            self.profiles.clear_default(user_id, except_id=profile.id)
        if values.get("is_default") is False and profile.is_default:
            raise ApplicationError(
                "DEFAULT_PROFILE_REQUIRED",
                "Choose another default profile before removing this default.",
                409,
            )
        for field, value in values.items():
            setattr(profile, field, value)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def delete(self, user_id: UUID, profile_id: UUID) -> None:
        profile = self.get(user_id, profile_id)
        was_default = profile.is_default
        self.profiles.delete(profile)
        self.session.flush()
        if was_default:
            remaining, _ = self.profiles.list_with_total(user_id)
            if remaining:
                remaining[0].is_default = True
        self.session.commit()

    @staticmethod
    def prompt_guidance(profile: WritingProfile) -> dict[str, Any]:
        return {
            "tone": profile.tone,
            "sentence_style": profile.sentence_style,
            "language": profile.language,
            "emoji_preference": profile.emoji_preference,
            "paragraph_length": profile.paragraph_length,
            "technical_depth": profile.technical_depth,
            "cta_preference": profile.cta_preference,
            "preferred_vocabulary": profile.preferred_vocabulary,
            "additional_guidance": profile.additional_guidance,
        }

    @staticmethod
    def _clean(values: dict[str, Any]) -> dict[str, Any]:
        optional = {
            "tone", "sentence_style", "emoji_preference", "paragraph_length",
            "technical_depth", "cta_preference",
        }
        for field in optional & values.keys():
            value = values[field]
            values[field] = value.strip() or None if isinstance(value, str) else value
        if values.get("preferred_vocabulary") is None:
            values["preferred_vocabulary"] = []
        return values

    @staticmethod
    def _validate_guidance(guidance: dict[str, Any]) -> None:
        if len(json.dumps(guidance)) > 10_000:
            raise ApplicationError(
                "WRITING_PROFILE_GUIDANCE_TOO_LARGE",
                "Additional guidance must be smaller than 10 KB.",
                422,
            )
