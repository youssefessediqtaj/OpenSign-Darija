from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.enums import LinguisticLanguage, LinguisticScript, LinguisticStatus
from app.models.linguistics import SemanticConcept
from app.services.linguistics.darija_renderer import entry_for_code, render_template
from app.services.linguistics.template_matcher import match_template
from app.services.linguistics.translation_renderer import render_translation
from app.services.linguistics.versioning import current_versions


@dataclass(frozen=True)
class GenerationInput:
    concept_codes: list[str]
    target_languages: list[str]
    politeness: str = "neutral"
    latin_variant: str = "standard"


class LinguisticEngine:
    strategy = "template_rules"

    def generate(
        self,
        db: Session,
        concepts: list[SemanticConcept],
        request: GenerationInput,
    ) -> dict[str, object]:
        concepts_by_code = {concept.code: concept for concept in concepts if concept.is_active}
        sequence = [code for code in request.concept_codes if code in concepts_by_code]
        match = match_template(db, sequence)
        versions = current_versions()
        warnings: list[str] = []
        system_insertions: list[str] = []
        alternatives: list[dict[str, str]] = []
        result = {"darija_arabic": "", "darija_latin": "", "french": "", "english": ""}

        if match.template:
            rendered = render_template(
                db,
                concepts_by_code,
                match.template.template_structure,
                request.latin_variant,
            )
            result["darija_arabic"] = rendered["darija_arabic"]
            result["darija_latin"] = rendered["darija_latin"]
            result["french"] = render_translation(
                db,
                concepts_by_code,
                str(match.template.template_structure.get("french", "")),
                LinguisticLanguage.FRENCH,
            )
            result["english"] = render_translation(
                db,
                concepts_by_code,
                str(match.template.template_structure.get("english", "")),
                LinguisticLanguage.ENGLISH,
            )
            alternatives = [
                {
                    "template": template.code,
                    **render_template(
                        db, concepts_by_code, template.template_structure, request.latin_variant
                    ),
                }
                for template in match.alternatives
            ]
        elif match.status == LinguisticStatus.INCOMPLETE.value:
            warnings.append(f"Phrase incomplete: ajoutez {', '.join(match.missing)}.")
            if sequence:
                first = sequence[0]
                result["darija_arabic"] = entry_for_code(
                    db, concepts_by_code, first, script=LinguisticScript.ARABIC
                )
                result["darija_latin"] = entry_for_code(
                    db, concepts_by_code, first, script=LinguisticScript.LATIN
                )
        elif sequence:
            warnings.append("Aucun template complet ne correspond a cette sequence.")
            first = sequence[0]
            result["darija_arabic"] = entry_for_code(
                db, concepts_by_code, first, script=LinguisticScript.ARABIC
            )
            result["darija_latin"] = entry_for_code(
                db, concepts_by_code, first, script=LinguisticScript.LATIN
            )
        else:
            warnings.append("Ajoutez au moins un signe confirme ou un mot manuel.")

        sensitive = any(
            concept.concept_type.value in {"HEALTH", "EMERGENCY"}
            or concept.code.startswith(("HEALTH_", "EMERGENCY_"))
            for concept in concepts_by_code.values()
        )
        if sensitive:
            warnings.append(
                "Verifiez attentivement ce message. "
                "OpenSign Darija ne remplace pas un interprete professionnel."
            )

        return {
            "generation_version": versions.engine,
            "dictionary_version": versions.dictionary,
            "template_version": versions.templates,
            "strategy": self.strategy,
            "semantic_sequence": sequence,
            "result": result,
            "template": match.template.code if match.template else None,
            "linguistic_status": match.status,
            "system_insertions": system_insertions,
            "warnings": warnings,
            "alternatives": alternatives,
        }
