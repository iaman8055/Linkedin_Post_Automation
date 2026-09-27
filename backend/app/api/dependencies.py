from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.errors import ApplicationError
from app.core.security import AccessTokenError, decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    session: DatabaseSession,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApplicationError("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except AccessTokenError as exc:
        raise ApplicationError(
            "INVALID_ACCESS_TOKEN", "Invalid or expired access token.", 401
        ) from exc

    user = session.get(User, user_id)
    if user is None:
        raise ApplicationError("INVALID_ACCESS_TOKEN", "Invalid or expired access token.", 401)
    if not user.is_active:
        raise ApplicationError("ACCOUNT_DISABLED", "This account is disabled.", 403)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
