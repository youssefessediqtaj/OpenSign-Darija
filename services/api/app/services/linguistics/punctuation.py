def normalize_arabic_punctuation(text: str, question: bool = False) -> str:
    stripped = " ".join(text.split())
    if not stripped:
        return stripped
    if question and not stripped.endswith("؟"):
        return f"{stripped}؟"
    return stripped
