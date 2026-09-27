from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApplicationError
from app.models.enums import TemplateStatus
from app.models.template import Template
from app.repositories.template import TemplateRepository
from app.schemas.template import TemplateCreate, TemplateUpdate

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Za-z][A-Za-z0-9_]*)\s*}}")


class TemplateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.templates = TemplateRepository(session)

    def create(self, user_id: UUID, payload: TemplateCreate) -> Template:
        placeholders = self._extract_placeholders(payload.body)
        template = self.templates.create_for_user(
            user_id,
            name=payload.name,
            description=self._optional(payload.description),
            body=payload.body,
            placeholders=placeholders,
            settings=payload.settings,
            status=TemplateStatus.ACTIVE,
        )
        self.session.commit()
        self.session.refresh(template)
        return template

    def list_templates(
        self, user_id: UUID, *, status: TemplateStatus | None, search: str | None,
        offset: int, limit: int
    ) -> tuple[list[Template], int]:
        return self.templates.list_filtered_for_user(
            user_id,
            status=status,
            search=search.strip() if search else None,
            offset=offset,
            limit=limit,
        )

    def get(self, user_id: UUID, template_id: UUID) -> Template:
        template = self.templates.get_for_user(template_id, user_id)
        if template is None:
            raise ApplicationError("TEMPLATE_NOT_FOUND", "Template not found.", 404)
        return template

    def update(self, user_id: UUID, template_id: UUID, payload: TemplateUpdate) -> Template:
        template = self.get(user_id, template_id)
        changes = payload.model_dump(exclude_unset=True)
        if "description" in changes:
            changes["description"] = self._optional(changes["description"])
        if "body" in changes:
            changes["placeholders"] = self._extract_placeholders(changes["body"])
        for field, value in changes.items():
            setattr(template, field, value)
        self.session.commit()
        self.session.refresh(template)
        return template

    def set_status(
        self, user_id: UUID, template_id: UUID, status: TemplateStatus
    ) -> Template:
        template = self.get(user_id, template_id)
        template.status = status
        self.session.commit()
        self.session.refresh(template)
        return template

    def delete(self, user_id: UUID, template_id: UUID) -> None:
        template = self.get(user_id, template_id)
        self.templates.delete(template)
        self.session.commit()

    def render(self, user_id: UUID, template_id: UUID, values: dict[str, str]) -> str:
        template = self.get(user_id, template_id)
        if template.status != TemplateStatus.ACTIVE:
            raise ApplicationError("TEMPLATE_ARCHIVED", "Archived templates cannot be used.", 409)
        missing = [name for name in template.placeholders if name not in values]
        unknown = sorted(set(values) - set(template.placeholders))
        if missing:
            raise ApplicationError(
                "TEMPLATE_VALUES_MISSING",
                f"Missing values for: {', '.join(missing)}.",
                422,
            )
        if unknown:
            raise ApplicationError(
                "TEMPLATE_VALUES_UNKNOWN",
                f"Unknown template values: {', '.join(unknown)}.",
                422,
            )
        rendered = PLACEHOLDER_PATTERN.sub(lambda match: values[match.group(1)], template.body)
        if len(rendered) > 3000:
            raise ApplicationError(
                "TEMPLATE_OUTPUT_TOO_LONG", "Rendered post exceeds 3,000 characters.", 422
            )
        return rendered

    @staticmethod
    def _extract_placeholders(body: str) -> list[str]:
        placeholders = list(dict.fromkeys(PLACEHOLDER_PATTERN.findall(body)))
        stripped = PLACEHOLDER_PATTERN.sub("", body)
        if "{{" in stripped or "}}" in stripped:
            raise ApplicationError(
                "TEMPLATE_SYNTAX_INVALID",
                "Placeholders must use names such as {{topic}}.",
                422,
            )
        if len(placeholders) > 50:
            raise ApplicationError(
                "TEMPLATE_PLACEHOLDER_LIMIT", "Templates support up to 50 placeholders.", 422
            )
        return placeholders

    @staticmethod
    def _optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
