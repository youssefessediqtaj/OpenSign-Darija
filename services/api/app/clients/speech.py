from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import ApiError


class SpeechServiceClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def synthesize(
        self, text: str, language: str, voice_id: str, speed: float, output_format: str
    ) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.settings.speech_service_url}/synthesize",
                json={
                    "text": text,
                    "language": language,
                    "voice_id": voice_id,
                    "speed": speed,
                    "output_format": output_format,
                },
                timeout=self.settings.speech_generation_timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise ApiError(
                "SPEECH_SERVICE_UNAVAILABLE", "Le service vocal est indisponible.", 503
            ) from exc
        if response.status_code >= 400:
            code = "SPEECH_GENERATION_FAILED"
            try:
                detail = response.json().get("detail", {})
                if isinstance(detail, dict) and detail.get("code"):
                    code = str(detail["code"])
            except ValueError:
                pass
            status_code = 404 if code == "VOICE_NOT_FOUND" else 422
            raise ApiError(code, "La generation vocale a echoue.", status_code)
        return dict(response.json())
