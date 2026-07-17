from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.linguistics import LinguisticEntry, SemanticConcept, SignSemanticMapping


def concepts_for_sign(db: Session, sign_id: str) -> list[SemanticConcept]:
    mappings = db.scalars(
        select(SignSemanticMapping)
        .where(SignSemanticMapping.sign_id == sign_id, SignSemanticMapping.is_default.is_(True))
        .order_by(SignSemanticMapping.priority.asc())
    ).all()
    concepts: list[SemanticConcept] = []
    for mapping in mappings:
        concept = db.get(SemanticConcept, mapping.semantic_concept_id)
        if concept and concept.is_active:
            concepts.append(concept)
    return concepts


def default_entry(
    db: Session,
    concept_id: str,
    language: str,
    script: str,
    variant: str = "default",
) -> str | None:
    entry = db.scalar(
        select(LinguisticEntry).where(
            LinguisticEntry.semantic_concept_id == concept_id,
            LinguisticEntry.language == language,
            LinguisticEntry.script == script,
            LinguisticEntry.is_active.is_(True),
            LinguisticEntry.is_default.is_(True),
        )
    )
    if entry:
        return entry.value
    if variant != "default":
        return default_entry(db, concept_id, language, script, "default")
    return None
