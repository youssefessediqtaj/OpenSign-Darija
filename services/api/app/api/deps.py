from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.session import get_db
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
