from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.enums import UserRoleName
from app.models.user import Role, User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, decode_token


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=[user_role.role.name for user_role in user.roles],
    )


def register_user(db: Session, payload: RegisterRequest) -> UserResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise ApiError("EMAIL_ALREADY_REGISTERED", "Cette adresse e-mail est deja utilisee.", 409)

    role = db.scalar(select(Role).where(Role.name == UserRoleName.USER.value))
    if role is None:
        role = Role(name=UserRoleName.USER.value, description="Compte utilisateur standard")
        db.add(role)
        db.flush()

    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    user.roles.append(UserRole(role=role))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_to_response(user)


def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise ApiError("INVALID_CREDENTIALS", "Identifiants invalides.", 401)
    if not user.is_active:
        raise ApiError("ACCOUNT_DISABLED", "Ce compte est desactive.", 403)
    return TokenResponse(
        access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id)
    )


def refresh_tokens(refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token, "refresh")
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ApiError("UNAUTHORIZED", "Token invalide.", 401)
    return TokenResponse(
        access_token=create_access_token(subject), refresh_token=create_refresh_token(subject)
    )
