from datetime import UTC, datetime

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import ApiError

_rate_limit_bucket: dict[str, list[float]] = {}


def clear_rate_limit_state() -> None:
    """Reset process-local state for deterministic tests."""
    _rate_limit_bucket.clear()


def recognition_payload_size_error(request: Request) -> ApiError | None:
    content_length = request.headers.get("content-length")
    if not content_length:
        return None
    try:
        received_bytes = int(content_length)
    except ValueError:
        return ApiError(
            "INVALID_CONTENT_LENGTH",
            "La taille de la requête est invalide.",
            400,
        )
    settings = get_settings()
    if received_bytes > settings.recognition_max_payload_bytes:
        return ApiError(
            "PAYLOAD_TOO_LARGE",
            "La sequence de mouvements est trop volumineuse.",
            413,
            {"max_bytes": settings.recognition_max_payload_bytes},
        )
    return None


def enforce_recognition_request_limits(request: Request) -> None:
    """Reject abusive requests before invoking inference.

    Recognition is anonymous and stateless. The deliberately process-local rate
    limiter bounds accidental abuse without introducing Redis, persistent visitor
    identifiers, or a new stateful runtime dependency.
    """

    payload_error = recognition_payload_size_error(request)
    if payload_error:
        raise payload_error
    settings = get_settings()
    client_key = request.client.host if request.client else "unknown-client"
    now = datetime.now(UTC).timestamp()
    window_start = now - 60
    entries = [
        entry for entry in _rate_limit_bucket.get(client_key, []) if entry > window_start
    ]
    if len(entries) >= settings.recognition_rate_limit:
        raise ApiError("RATE_LIMITED", "Trop de reconnaissances en peu de temps.", 429)
    entries.append(now)
    _rate_limit_bucket[client_key] = entries
