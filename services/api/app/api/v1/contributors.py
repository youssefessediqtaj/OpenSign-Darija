from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import ContributorProfile
from app.models.enums import UserRoleName
from app.models.user import Role, User, UserRole
from app.schemas.dataset import ContributorProfileRequest, ContributorProfileResponse

router = APIRouter(prefix="/contributors", tags=["contributors"])


def next_public_id(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(ContributorProfile)) or 0
    return f"signer_{count + 1:06d}"


def grant_contributor_role(db: Session, user: User) -> None:
    if any(user_role.role.name == UserRoleName.CONTRIBUTOR.value for user_role in user.roles):
        return
    role = db.scalar(select(Role).where(Role.name == UserRoleName.CONTRIBUTOR.value))
    if role is None:
        role = Role(name=UserRoleName.CONTRIBUTOR.value, description="Contribution aux donnees")
        db.add(role)
        db.flush()
    user.roles.append(UserRole(role=role))


@router.get("/me", response_model=ContributorProfileResponse)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorProfile:
    profile = db.scalar(
        select(ContributorProfile).where(ContributorProfile.user_id == current_user.id)
    )
    if profile is None:
        raise ApiError("NOT_FOUND", "Profil contributeur introuvable.", 404)
    return profile


@router.post("/me", response_model=ContributorProfileResponse, status_code=201)
def create_my_profile(
    payload: ContributorProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorProfile:
    existing = db.scalar(
        select(ContributorProfile).where(ContributorProfile.user_id == current_user.id)
    )
    if existing is not None:
        return existing
    profile = ContributorProfile(
        user_id=current_user.id,
        public_id=next_public_id(db),
        **payload.model_dump(),
    )
    db.add(profile)
    grant_contributor_role(db, current_user)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/me", response_model=ContributorProfileResponse)
def update_my_profile(
    payload: ContributorProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ContributorProfile:
    profile = db.scalar(
        select(ContributorProfile).where(ContributorProfile.user_id == current_user.id)
    )
    if profile is None:
        raise ApiError("NOT_FOUND", "Profil contributeur introuvable.", 404)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
