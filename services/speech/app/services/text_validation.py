import re


def validate_text(text: str, min_length: int, max_length: int, max_sentences: int) -> None:
    useful = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)
    if len(useful) < min_length:
        raise ValueError("EMPTY_TEXT")
    if len(text) > max_length:
        raise ValueError("TEXT_TOO_LONG")
    sentence_count = len([part for part in re.split(r"[.!?؟]+", text) if part.strip()])
    if sentence_count > max_sentences:
        raise ValueError("TOO_MANY_SENTENCES")
    if re.search(r"[<>]{2,}|<script|javascript:", text, flags=re.IGNORECASE):
        raise ValueError("UNSUPPORTED_TEXT")
