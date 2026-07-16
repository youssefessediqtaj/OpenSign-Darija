from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ApiError
from app.db.session import get_db
from app.models.sign import Sign, SignCategory
from app.schemas.signs import CategoryResponse, PaginatedSignsResponse, SignResponse

router = APIRouter(tags=["signs"])


def sign_to_response(sign: Sign) -> SignResponse:
    return SignResponse(
        id=sign.id,
        code=sign.code,
        slug=sign.slug,
        canonical_meaning=sign.canonical_meaning,
        darija_arabic=sign.darija_arabic,
        darija_latin=sign.darija_latin,
        french_translation=sign.french_translation,
        english_translation=sign.english_translation,
        category=CategoryResponse(
            id=sign.category.id,
            slug=sign.category.slug,
            name_fr=sign.category.name_fr,
            name_ar=sign.category.name_ar,
            name_en=sign.category.name_en,
            description=sign.category.description,
        ),
        status=sign.status,
        risk_level=sign.risk_level,
        is_active=sign.is_active,
    )


@router.get("/signs", response_model=PaginatedSignsResponse)
def list_signs(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=80),
    category: str | None = Query(default=None, max_length=80),
) -> PaginatedSignsResponse:
    statement = select(Sign).options(selectinload(Sign.category)).where(Sign.is_active.is_(True))
    count_statement = select(func.count()).select_from(Sign).where(Sign.is_active.is_(True))
    if search:
        term = f"%{search.strip().lower()}%"
        statement = statement.where(
            func.lower(Sign.canonical_meaning).like(term) | func.lower(Sign.darija_latin).like(term)
        )
        count_statement = count_statement.where(
            func.lower(Sign.canonical_meaning).like(term) | func.lower(Sign.darija_latin).like(term)
        )
    if category:
        statement = statement.join(SignCategory).where(SignCategory.slug == category)
        count_statement = count_statement.join(SignCategory).where(SignCategory.slug == category)
    total = db.scalar(count_statement) or 0
    signs = db.scalars(
        statement.order_by(Sign.canonical_meaning).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PaginatedSignsResponse(
        items=[sign_to_response(sign) for sign in signs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/signs/{sign_id}", response_model=SignResponse)
def get_sign(sign_id: str, db: Annotated[Session, Depends(get_db)]) -> SignResponse:
    sign = db.scalar(select(Sign).options(selectinload(Sign.category)).where(Sign.id == sign_id))
    if sign is None:
        raise ApiError("NOT_FOUND", "Signe introuvable.", 404)
    return sign_to_response(sign)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Annotated[Session, Depends(get_db)]) -> list[CategoryResponse]:
    categories = db.scalars(select(SignCategory).order_by(SignCategory.name_fr)).all()
    return [
        CategoryResponse.model_validate(category, from_attributes=True) for category in categories
    ]
