from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.linguistics import MessageTemplate, SemanticConcept
from app.schemas.messages import ConceptResponse, LinguisticTemplateResponse

router = APIRouter(prefix="/linguistics", tags=["linguistics"])


@router.get("/version")
def linguistic_version() -> dict[str, str]:
    settings = get_settings()
    return {
        "engine_mode": settings.linguistic_engine_mode,
        "engine_version": settings.linguistic_engine_version,
        "dictionary_version": settings.linguistic_dictionary_version,
        "template_version": settings.linguistic_template_version,
    }


@router.get("/concepts", response_model=list[ConceptResponse])
def list_concepts(db: Annotated[Session, Depends(get_db)]) -> list[ConceptResponse]:
    concepts = db.scalars(select(SemanticConcept).order_by(SemanticConcept.code)).all()
    return [
        ConceptResponse(
            id=concept.id,
            code=concept.code,
            name_fr=concept.name_fr,
            name_en=concept.name_en,
            concept_type=concept.concept_type.value,
            is_active=concept.is_active,
        )
        for concept in concepts
    ]


@router.get("/templates", response_model=list[LinguisticTemplateResponse])
def list_templates(db: Annotated[Session, Depends(get_db)]) -> list[LinguisticTemplateResponse]:
    templates = db.scalars(select(MessageTemplate).order_by(MessageTemplate.code)).all()
    return [
        LinguisticTemplateResponse(
            id=template.id,
            code=template.code,
            name_fr=template.name_fr,
            name_ar=template.name_ar,
            name_en=template.name_en,
            category=template.category,
            risk_level=template.risk_level.value,
            version=template.version,
            is_active=template.is_active,
        )
        for template in templates
    ]
