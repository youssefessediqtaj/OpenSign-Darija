from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.linguistics import MessageTemplate


@dataclass(frozen=True)
class TemplateMatch:
    template: MessageTemplate | None
    status: str
    alternatives: list[MessageTemplate]
    missing: list[str]
    reason: str


def concept_type_map(codes: list[str]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for code in codes:
        if code.startswith("ACTION_"):
            mapped["ACTION"] = code
        elif code.startswith("OBJECT_"):
            mapped["OBJECT"] = code
        elif code.startswith("PERSON_"):
            mapped["PERSON"] = code
        elif code.startswith("QUESTION_"):
            mapped["QUESTION"] = code
        elif code.startswith("HEALTH_"):
            mapped["HEALTH"] = code
        elif code.startswith("REQUEST_"):
            mapped["REQUEST"] = code
        elif code.startswith("POLITENESS_"):
            mapped["POLITENESS"] = code
        elif code.startswith("AFFIRMATION_"):
            mapped["AFFIRMATION"] = code
        elif code.startswith("NEGATION_"):
            mapped["NEGATION"] = code
        elif code.startswith("EMERGENCY_"):
            mapped["EMERGENCY"] = code
    return mapped


def match_template(db: Session, concept_codes: list[str]) -> TemplateMatch:
    templates = db.scalars(select(MessageTemplate).where(MessageTemplate.is_active.is_(True))).all()
    code_set = set(concept_codes)
    typed = concept_type_map(concept_codes)
    candidates: list[MessageTemplate] = []
    incomplete: list[str] = []
    for template in templates:
        structure = template.template_structure
        raw_required = structure.get("required", [])
        required = [str(item) for item in raw_required] if isinstance(raw_required, list) else []
        if all(item in code_set or item in typed for item in required):
            candidates.append(template)
            continue
        present = [item for item in required if item in code_set or item in typed]
        if present:
            incomplete.extend(
                item for item in required if item not in code_set and item not in typed
            )
    if len(candidates) > 1:
        return TemplateMatch(candidates[0], "AMBIGUOUS", candidates[:3], [], "multiple_templates")
    if candidates:
        return TemplateMatch(candidates[0], "HIGH", [], [], "matched")
    if incomplete:
        return TemplateMatch(None, "INCOMPLETE", [], sorted(set(incomplete)), "missing_required")
    return TemplateMatch(None, "LOW", [], [], "no_template")
