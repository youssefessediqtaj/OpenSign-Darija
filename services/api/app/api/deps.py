from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.session import get_db
from app.models.enums import UserRoleName
from app.models.user import User
from app.security.tokens import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise ApiError("UNAUTHORIZED", "Authentification requise.", 401)
    payload = decode_token(credentials.credentials)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ApiError("UNAUTHORIZED", "Token invalide.", 401)
    user = db.scalar(select(User).where(User.id == subject))
    if user is None:
        raise ApiError("UNAUTHORIZED", "Utilisateur introuvable.", 401)
    return user


def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    return get_current_user(credentials, db)


def user_role_names(user: User) -> set[str]:
    return {user_role.role.name for user_role in user.roles}


def require_roles(*roles: UserRoleName) -> Callable[[User], User]:
    allowed = {role.value for role in roles}

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not user_role_names(current_user).intersection(allowed):
            raise ApiError("FORBIDDEN", "Permission insuffisante.", 403)
        return current_user

    return dependency


def require_any_reviewer(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRoleName.LINGUIST_REVIEWER,
                UserRoleName.ML_REVIEWER,
                UserRoleName.ADMIN,
            )
        ),
    ],
) -> User:
    return current_user
