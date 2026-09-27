from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.core.errors import ApplicationError
from app.schemas.linkedin import (
    LinkedInAccountResponse,
    LinkedInAuthorizationResponse,
    LinkedInConnectionListResponse,
    LinkedInTestPostRequest,
    LinkedInTestPostResponse,
)
from app.services.linkedin.client import LinkedInClient
from app.services.linkedin.service import LinkedInService
from app.services.publishing.test_post import TestPostPublisher

router = APIRouter(prefix="/linkedin")


def get_linkedin_client() -> LinkedInClient:
    return LinkedInClient()


def get_linkedin_service(
    session: DatabaseSession,
    settings: AppSettings,
    client: Annotated[LinkedInClient, Depends(get_linkedin_client)],
) -> LinkedInService:
    return LinkedInService(session, settings, client)


LinkedInServiceDependency = Annotated[LinkedInService, Depends(get_linkedin_service)]


@router.get("/connect", response_model=LinkedInAuthorizationResponse)
def connect(user: CurrentUser, service: LinkedInServiceDependency) -> LinkedInAuthorizationResponse:
    return LinkedInAuthorizationResponse(authorization_url=service.create_authorization_url(user))


@router.get("/callback", response_model=LinkedInAccountResponse)
def callback(
    service: LinkedInServiceDependency,
    state_value: Annotated[str, Query(alias="state", min_length=16)],
    code: Annotated[str | None, Query(min_length=1)] = None,
    error: str | None = None,
) -> LinkedInAccountResponse:
    if error is not None:
        service.validate_denied_state(state_value)
        raise ApplicationError(
            "LINKEDIN_AUTHORIZATION_DENIED", "LinkedIn authorization denied.", 400
        )
    if code is None:
        raise ApplicationError(
            "LINKEDIN_AUTHORIZATION_CODE_MISSING", "Authorization code missing.", 400
        )
    return LinkedInAccountResponse.model_validate(service.complete_connection(code, state_value))


@router.get("/status", response_model=LinkedInConnectionListResponse)
def connection_status(
    user: CurrentUser, service: LinkedInServiceDependency
) -> LinkedInConnectionListResponse:
    accounts = [
        LinkedInAccountResponse.model_validate(account)
        for account in service.list_accounts(user.id)
    ]
    return LinkedInConnectionListResponse(accounts=accounts)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(
    account_id: UUID, user: CurrentUser, service: LinkedInServiceDependency
) -> Response:
    service.disconnect(user.id, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{account_id}/test-post", response_model=LinkedInTestPostResponse)
def publish_test_post(
    account_id: UUID,
    payload: LinkedInTestPostRequest,
    user: CurrentUser,
    service: LinkedInServiceDependency,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)],
) -> LinkedInTestPostResponse:
    publisher = TestPostPublisher(service.session, service.settings, service.client)
    post = publisher.publish(
        user_id=user.id,
        account_id=account_id,
        commentary=payload.commentary,
        idempotency_key=idempotency_key,
    )
    assert post.linkedin_post_id is not None and post.published_at is not None
    return LinkedInTestPostResponse(
        id=post.id,
        linkedin_post_id=post.linkedin_post_id,
        status=post.status.value,
        published_at=post.published_at,
    )
