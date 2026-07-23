import re
import unicodedata
from dataclasses import dataclass, field


ARABIZI_WORDS = {
    "3afak": "عافاك",
    "3awnouni": "عاونوني",
    "bghit": "بغيت",
    "lma": "الما",
    "fin": "فين",
    "tbib": "الطبيب",
    "shukran": "شكرا",
    "awnouni": "عاونوني",
}

ABBREVIATIONS = {
    "د.": "دكتور",
    "mr": "مستر",
}

DIGITS = str.maketrans("0123456789٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
NUMBER_WORDS = {
    "0": "صفر",
    "1": "واحد",
    "2": "جوج",
    "3": "ثلاثة",
    "4": "ربعة",
    "5": "خمسة",
    "6": "ستة",
    "7": "سبعة",
    "8": "ثمانية",
    "9": "تسعود",
    "10": "عشرة",
    "20": "عشرين",
}


@dataclass(frozen=True)
class NormalizedText:
    original_text: str
    normalized_text: str
    normalization_version: str
    unknown_tokens: list[str] = field(default_factory=list)


def _normalize_numbers(text: str) -> str:
    text = text.translate(DIGITS)

    def phone(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        return " ".join(NUMBER_WORDS.get(char, char) for char in digits)

    text = re.sub(r"\b0[5-7](?:[\s.-]?\d{2}){4}\b", phone, text)

    def amount(match: re.Match[str]) -> str:
        number = match.group(1)
        spoken = NUMBER_WORDS.get(number, " ".join(NUMBER_WORDS.get(char, char) for char in number))
        return f"{spoken} درهم"

    text = re.sub(r"\b(\d+)\s*درهم\b", amount, text)
    return re.sub(r"\b\d+\b", lambda m: NUMBER_WORDS.get(m.group(0), m.group(0)), text)


def normalize_darija(text: str, version: str = "darija-normalizer-1.0.0") -> NormalizedText:
    original = text
    text = unicodedata.normalize("NFKC", text)
    text = "".join(char for char in text if unicodedata.category(char) not in {"Cf", "Cc"})
    for source, replacement in ABBREVIATIONS.items():
        text = text.replace(source, replacement)
    text = _normalize_numbers(text)
    text = re.sub(r"([!?؟.,،:؛])\1+", r"\1", text)
    text = re.sub(r"([^\W\d_])\1{3,}", r"\1\1", text, flags=re.UNICODE)
    unknown: list[str] = []
    tokens: list[str] = []
    for token in re.split(r"(\s+)", text):
        lowered = token.lower()
        if lowered in ARABIZI_WORDS:
            tokens.append(ARABIZI_WORDS[lowered])
        else:
            if re.search(r"[a-zA-Z]", token) and lowered.strip(".,!?") not in ARABIZI_WORDS:
                unknown.append(token.strip(".,!?"))
            tokens.append(token)
    text = "".join(tokens)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([!?؟.,،:؛])", r"\1", text)
    return NormalizedText(
        original_text=original,
        normalized_text=text,
        normalization_version=version,
        unknown_tokens=[token for token in unknown if token],
    )
