from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models.enums import ScheduleStatus
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.services.scheduling import SchedulingService

router = APIRouter(prefix="/schedules")


def get_scheduling_service(session: DatabaseSession) -> SchedulingService:
    return SchedulingService(session)


SchedulingServiceDependency = Annotated[SchedulingService, Depends(get_scheduling_service)]


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    payload: ScheduleCreate, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.create(user.id, payload))


@router.get("", response_model=ScheduleListResponse)
def list_schedules(
    user: CurrentUser,
    service: SchedulingServiceDependency,
    schedule_status: Annotated[ScheduleStatus | None, Query(alias="status")] = None,
    start: datetime | None = None,
    end: datetime | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ScheduleListResponse:
    schedules, total = service.list(
        user.id, status=schedule_status, start=start, end=end, offset=offset, limit=limit
    )
    return ScheduleListResponse(items=schedules, total=total, offset=offset, limit=limit)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: UUID, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.get(user.id, schedule_id))


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def reschedule(
    schedule_id: UUID,
    payload: ScheduleUpdate,
    user: CurrentUser,
    service: SchedulingServiceDependency,
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.reschedule(user.id, schedule_id, payload))


@router.post("/{schedule_id}/cancel", response_model=ScheduleResponse)
def cancel_schedule(
    schedule_id: UUID, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.cancel(user.id, schedule_id))


@router.post("/{schedule_id}/pause", response_model=ScheduleResponse)
def pause_schedule(
    schedule_id: UUID, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.pause(user.id, schedule_id))


@router.post("/{schedule_id}/resume", response_model=ScheduleResponse)
def resume_schedule(
    schedule_id: UUID, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.resume(user.id, schedule_id))


@router.post("/{schedule_id}/retry", response_model=ScheduleResponse)
def retry_failed_schedule(
    schedule_id: UUID, user: CurrentUser, service: SchedulingServiceDependency
) -> ScheduleResponse:
    return ScheduleResponse.model_validate(service.retry_failed(user.id, schedule_id))
