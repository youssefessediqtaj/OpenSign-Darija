from datetime import UTC, datetime

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import ApiError

_contribution_rate_limit_bucket: dict[str, list[float]] = {}


def clear_contribution_rate_limits() -> None:
    _contribution_rate_limit_bucket.clear()


def contribution_payload_size_error(request: Request) -> ApiError | None:
    content_length = request.headers.get("content-length")
    if not content_length:
        return None
    try:
        received_bytes = int(content_length)
    except ValueError:
        return ApiError("INVALID_CONTENT_LENGTH", "La taille de la requête est invalide.", 400)
    maximum = get_settings().contribution_max_video_bytes + 128_000
    if received_bytes > maximum:
        return ApiError(
            "PAYLOAD_TOO_LARGE",
            "La contribution dépasse la taille maximale autorisée.",
            413,
            {"max_bytes": maximum},
        )
    return None


def enforce_contribution_rate_limit(request: Request) -> None:
    settings = get_settings()
    client_key = request.client.host if request.client else "unknown-client"
    now = datetime.now(UTC).timestamp()
    entries = [
        entry for entry in _contribution_rate_limit_bucket.get(client_key, []) if entry > now - 60
    ]
    if len(entries) >= settings.contribution_rate_limit:
        raise ApiError("RATE_LIMITED", "Trop de contributions en peu de temps.", 429)
    entries.append(now)
    _contribution_rate_limit_bucket[client_key] = entries
