from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TATWEEL = "\u0640"
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
SIGN_SUFFIX_RE = re.compile(
    r"\s*\(\s*"
    r"إ[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*"
    r"ش[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*"
    r"ا[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*"
    r"ر[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*"
    r"ة[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]*"
    r"\s+([0-9٠-٩]+)\s*\)\s*$"
)


@dataclass(frozen=True)
class ParsedMoslLabel:
    raw_label: str
    normalized_label_ar: str
    label_key: str
    variant_index: int


def strip_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[0]


def remove_trailing_variant(raw_label: str) -> tuple[str, int]:
    text = unicodedata.normalize("NFC", raw_label).strip()
    match = SIGN_SUFFIX_RE.search(text)
    if match is None:
        return text, 1
    variant = int(match.group(1).translate(ARABIC_DIGITS))
    return text[: match.start()].strip(), variant


def normalize_arabic_key(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).replace(TATWEEL, "")
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ٱ", "ا")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
    )
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text


def parse_mosl_label(filename_or_stem: str) -> ParsedMoslLabel:
    raw = strip_extension(filename_or_stem)
    raw = unicodedata.normalize("NFC", raw).strip()
    display, variant = remove_trailing_variant(raw)
    return ParsedMoslLabel(
        raw_label=raw,
        normalized_label_ar=display,
        label_key=normalize_arabic_key(display),
        variant_index=variant,
    )
