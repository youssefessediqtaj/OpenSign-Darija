FALLBACK_MAP = {
    "بغيت": "bghit",
    "الما": "lma",
    "فين": "fin",
    "كاين": "kayn",
    "الطبيب": "tbib",
    "عاونوني": "3awnouni",
    "شكرا": "shukran",
    "إيه": "iyeh",
    "لا": "la",
    "مستعجل": "mestaajel",
    "الألم": "lalam",
}


def latinize(text: str, variant: str = "standard") -> str:
    words = text.replace("؟", " ؟").replace(".", " .").split()
    rendered = [FALLBACK_MAP.get(word, word) for word in words]
    result = " ".join(rendered).replace(" ؟", "?").replace(" .", ".")
    if variant == "arabizi":
        return result.replace("awnouni", "3awnouni").replace("lalam", "l2alam")
    return result.replace("3awnouni", "awnouni")
