from pydantic import BaseModel, Field

from app.models.enums import RiskLevel, SignStatus


class CategoryResponse(BaseModel):
    id: str
    slug: str
    name_fr: str
    name_ar: str
    name_en: str
    description: str


class SignResponse(BaseModel):
    id: str
    code: str
    slug: str
    canonical_meaning: str
    darija_arabic: str
    darija_latin: str
    french_translation: str
    english_translation: str
    category: CategoryResponse
    status: SignStatus
    risk_level: RiskLevel
    is_active: bool


class PaginatedSignsResponse(BaseModel):
    items: list[SignResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
