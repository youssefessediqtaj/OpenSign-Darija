from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

import jwt

from app.core.config import get_settings
from app.core.errors import ApiError

TokenType = Literal["access", "refresh"]


def create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    return create_token(
        subject, "access", timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    return create_token(subject, "refresh", timedelta(days=settings.jwt_refresh_token_expire_days))


def decode_token(token: str, expected_type: TokenType = "access") -> dict[str, object]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ApiError("UNAUTHORIZED", "Token invalide ou expire.", 401) from exc
    if payload.get("type") != expected_type:
        raise ApiError("UNAUTHORIZED", "Type de token invalide.", 401)
    return payload
