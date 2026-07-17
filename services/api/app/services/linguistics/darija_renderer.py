from sqlalchemy.orm import Session

from app.models.enums import LinguisticLanguage, LinguisticScript
from app.models.linguistics import SemanticConcept
from app.services.linguistics.concept_resolver import default_entry
from app.services.linguistics.latin_transliterator import latinize
from app.services.linguistics.punctuation import normalize_arabic_punctuation
from app.services.linguistics.template_matcher import concept_type_map


def entry_for_code(
    db: Session,
    concepts_by_code: dict[str, SemanticConcept],
    code_or_slot: str,
    script: LinguisticScript,
    latin_variant: str = "standard",
) -> str:
    typed = concept_type_map(list(concepts_by_code))
    code = typed.get(code_or_slot, code_or_slot)
    concept = concepts_by_code.get(code)
    if not concept:
        return ""
    variant = "arabizi" if latin_variant == "arabizi" else "default"
    value = default_entry(db, concept.id, LinguisticLanguage.DARIJA.value, script.value, variant)
    return value or concept.name_fr


def render_template(
    db: Session,
    concepts_by_code: dict[str, SemanticConcept],
    structure: dict[str, object],
    latin_variant: str = "standard",
) -> dict[str, str]:
    arabic_pattern = str(structure.get("darija_arabic", ""))
    latin_pattern = str(structure.get("darija_latin", ""))
    replacements: dict[str, str] = {}
    replacements_latin: dict[str, str] = {}
    for placeholder in [
        "action",
        "object",
        "person",
        "question",
        "request",
        "health",
        "politeness",
        "emergency",
    ]:
        slot = placeholder.upper()
        replacements[placeholder] = entry_for_code(
            db, concepts_by_code, slot, LinguisticScript.ARABIC
        )
        replacements_latin[f"{placeholder}_latin"] = entry_for_code(
            db, concepts_by_code, slot, LinguisticScript.LATIN, latin_variant
        )
    arabic = arabic_pattern.format(**replacements)
    if latin_pattern:
        latin = latin_pattern.format(**replacements_latin)
    else:
        latin = latinize(arabic, latin_variant)
    is_question = "QUESTION" in concept_type_map(list(concepts_by_code))
    return {
        "darija_arabic": normalize_arabic_punctuation(arabic, question=is_question),
        "darija_latin": latin.strip(),
    }
