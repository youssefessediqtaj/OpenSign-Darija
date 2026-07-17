from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class LinguisticVersions:
    engine: str
    dictionary: str
    templates: str


def current_versions() -> LinguisticVersions:
    settings = get_settings()
    return LinguisticVersions(
        engine=settings.linguistic_engine_version,
        dictionary=settings.linguistic_dictionary_version,
        templates=settings.linguistic_template_version,
    )
