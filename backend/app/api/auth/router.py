from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.core.errors import ApplicationError
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPairResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import AuthService, TokenPair

router = APIRouter(prefix="/auth")


def get_auth_service(session: DatabaseSession, settings: AppSettings) -> AuthService:
    return AuthService(session, settings)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


def token_response(pair: TokenPair) -> TokenPairResponse:
    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, service: AuthServiceDependency) -> AuthResponse:
    user, pair = service.register(str(payload.email), payload.password, payload.display_name)
    return AuthResponse(user=UserResponse.model_validate(user), **token_response(pair).model_dump())


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, service: AuthServiceDependency) -> AuthResponse:
    user, pair = service.login(str(payload.email), payload.password)
    return AuthResponse(user=UserResponse.model_validate(user), **token_response(pair).model_dump())


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDependency) -> AuthResponse:
    user, pair = service.refresh(payload.refresh_token)
    return AuthResponse(user=UserResponse.model_validate(user), **token_response(pair).model_dump())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, service: AuthServiceDependency) -> Response:
    service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def current_user(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=UserResponse)
def verify_email(payload: VerifyEmailRequest, service: AuthServiceDependency) -> UserResponse:
    return UserResponse.model_validate(service.verify_email(payload.token))


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest, service: AuthServiceDependency
) -> MessageResponse:
    service.reset_password(payload.token, payload.new_password)
    return MessageResponse(message="Password has been reset.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(_: ForgotPasswordRequest) -> MessageResponse:
    raise ApplicationError(
        "EMAIL_DELIVERY_NOT_CONFIGURED",
        "Password-reset email delivery is not configured.",
        503,
    )


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(_: ForgotPasswordRequest) -> MessageResponse:
    raise ApplicationError(
        "EMAIL_DELIVERY_NOT_CONFIGURED",
        "Verification email delivery is not configured.",
        503,
    )

