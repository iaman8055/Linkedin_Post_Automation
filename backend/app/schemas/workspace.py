from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["personal", "company", "client"] = "personal"


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    kind: str
    is_default: bool
    is_active: bool
    is_current: bool = False


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceResponse]
    active_workspace_id: UUID
