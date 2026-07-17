from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata


@dataclass(frozen=True)
class AlphabetLabel:
    original_label: str
    normalized_label: str
    class_code: str
    arabic_letter: str | None
    review_status: str


LETTER_REFERENCES = {
    "alef": ("ARABIC_LETTER_ALEF", "ا"),
    "ا": ("ARABIC_LETTER_ALEF", "ا"),
    "baa": ("ARABIC_LETTER_BAA", "ب"),
    "ba": ("ARABIC_LETTER_BAA", "ب"),
    "ب": ("ARABIC_LETTER_BAA", "ب"),
    "taa": ("ARABIC_LETTER_TAA", "ت"),
    "ta": ("ARABIC_LETTER_TAA", "ت"),
    "ت": ("ARABIC_LETTER_TAA", "ت"),
}


def normalize_label(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().lower().replace(" ", "_")


def parse_label(path: Path, root: Path) -> AlphabetLabel:
    relative = path.relative_to(root)
    original = relative.parts[0] if len(relative.parts) > 1 else path.stem
    normalized = normalize_label(original)
    match = LETTER_REFERENCES.get(normalized)
    if match:
        return AlphabetLabel(original, normalized, match[0], match[1], "AUTO_MAPPED")
    return AlphabetLabel(
        original,
        normalized,
        f"UNREVIEWED_{normalized.upper()}",
        None,
        "REQUIRES_LINGUISTIC_REVIEW",
    )
