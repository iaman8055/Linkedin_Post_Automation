from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models.enums import TemplateStatus
from app.schemas.template import (
    TemplateCreate,
    TemplateListResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.templates import TemplateService

router = APIRouter(prefix="/templates")


def get_template_service(session: DatabaseSession) -> TemplateService:
    return TemplateService(session)


TemplateServiceDependency = Annotated[TemplateService, Depends(get_template_service)]


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate, user: CurrentUser, service: TemplateServiceDependency
) -> TemplateResponse:
    return TemplateResponse.model_validate(service.create(user.id, payload))


@router.get("", response_model=TemplateListResponse)
def list_templates(
    user: CurrentUser,
    service: TemplateServiceDependency,
    template_status: Annotated[TemplateStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TemplateListResponse:
    templates, total = service.list_templates(
        user.id, status=template_status, search=search, offset=offset, limit=limit
    )
    return TemplateListResponse(
        items=templates, total=total, offset=offset, limit=limit
    )


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: UUID, user: CurrentUser, service: TemplateServiceDependency
) -> TemplateResponse:
    return TemplateResponse.model_validate(service.get(user.id, template_id))


@router.patch("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: UUID,
    payload: TemplateUpdate,
    user: CurrentUser,
    service: TemplateServiceDependency,
) -> TemplateResponse:
    return TemplateResponse.model_validate(service.update(user.id, template_id, payload))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: UUID, user: CurrentUser, service: TemplateServiceDependency
) -> Response:
    service.delete(user.id, template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{template_id}/archive", response_model=TemplateResponse)
def archive_template(
    template_id: UUID, user: CurrentUser, service: TemplateServiceDependency
) -> TemplateResponse:
    return TemplateResponse.model_validate(
        service.set_status(user.id, template_id, TemplateStatus.ARCHIVED)
    )


@router.post("/{template_id}/restore", response_model=TemplateResponse)
def restore_template(
    template_id: UUID, user: CurrentUser, service: TemplateServiceDependency
) -> TemplateResponse:
    return TemplateResponse.model_validate(
        service.set_status(user.id, template_id, TemplateStatus.ACTIVE)
    )


@router.post("/{template_id}/render", response_model=TemplateRenderResponse)
def render_template(
    template_id: UUID,
    payload: TemplateRenderRequest,
    user: CurrentUser,
    service: TemplateServiceDependency,
) -> TemplateRenderResponse:
    return TemplateRenderResponse(content=service.render(user.id, template_id, payload.values))
