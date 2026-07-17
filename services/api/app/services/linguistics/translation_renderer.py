from sqlalchemy.orm import Session

from app.models.enums import LinguisticLanguage, LinguisticScript
from app.models.linguistics import SemanticConcept
from app.services.linguistics.concept_resolver import default_entry
from app.services.linguistics.template_matcher import concept_type_map


def render_translation(
    db: Session,
    concepts_by_code: dict[str, SemanticConcept],
    pattern: str,
    language: LinguisticLanguage,
) -> str:
    typed = concept_type_map(list(concepts_by_code))
    replacements: dict[str, str] = {}
    for placeholder in ["action", "object", "person", "question", "request", "health", "emergency"]:
        code = typed.get(placeholder.upper(), placeholder.upper())
        concept = concepts_by_code.get(code)
        replacements[placeholder] = (
            default_entry(db, concept.id, language.value, LinguisticScript.LATIN.value)
            or concept.name_fr
            if concept
            else ""
        )
    return pattern.format(**replacements).strip()
