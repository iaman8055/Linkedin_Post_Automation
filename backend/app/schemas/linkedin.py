from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LinkedInAuthorizationResponse(BaseModel):
    authorization_url: str


class LinkedInAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID | None
    linkedin_member_id: str
    display_name: str | None
    profile_image_url: str | None
    token_expires_at: datetime | None
    scopes: str
    is_connected: bool


class LinkedInConnectionListResponse(BaseModel):
    accounts: list[LinkedInAccountResponse]


class LinkedInTestPostRequest(BaseModel):
    commentary: str = Field(min_length=1, max_length=3000)


class LinkedInTestPostResponse(BaseModel):
    id: UUID
    linkedin_post_id: str
    status: str
    published_at: datetime
