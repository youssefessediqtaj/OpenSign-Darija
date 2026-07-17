from app.core.config import get_settings
from app.core.errors import ApiError


def validate_text_length(*texts: str | None) -> None:
    max_len = get_settings().message_max_text_length
    for text in texts:
        if text and len(text) > max_len:
            raise ApiError(
                "TEXT_TOO_LONG", "Le texte du message est trop long.", 413, {"max": max_len}
            )
