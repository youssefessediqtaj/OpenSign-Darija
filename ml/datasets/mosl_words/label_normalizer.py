from __future__ import annotations

import re
import unicodedata


def normalize_arabic_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    return text
