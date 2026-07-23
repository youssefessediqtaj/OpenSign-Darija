import base64
import wave
from collections.abc import Iterator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_speech_provider
from app.core.config import get_settings
from app.main import app
from app.providers.local import SynthesisInput, SynthesisOutput
from app.schemas.synthesis import SynthesisRequest, Voice
from app.services.synthesis_service import SynthesisService
from app.services.text_normalization import normalize_darija

client = TestClient(app)


def make_test_wav(sample_rate: int = 22_050) -> tuple[bytes, int]:
    duration_ms = 100
    frame_count = sample_rate * duration_ms // 1000
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x01\x00" * frame_count)
    return output.getvalue(), duration_ms


class InjectedSpeechProvider:
    def is_ready(self) -> bool:
        return True

    def list_voices(self) -> list[Voice]:
        return [
            Voice(
                id="darija-default",
                provider="test-arabic",
                voice_code="test-ar",
                display_name="Test Arabic voice",
                language="ar-MA",
                locale="ar-MA",
                description="Explicitly injected deterministic test voice",
                model_version="test-only",
                license="test-only",
                is_default=True,
            ),
            Voice(
                id="arabic-fallback",
                provider="test-arabic",
                voice_code="test-ar-fallback",
                display_name="Test Arabic fallback",
                language="ar",
                locale="ar",
                description="Explicitly injected deterministic fallback test voice",
                model_version="test-only",
                license="test-only",
            ),
        ]

    def synthesize(self, request: SynthesisInput) -> SynthesisOutput:
        assert request.text
        audio, _ = make_test_wav()
        return SynthesisOutput(
            audio_bytes=audio,
            provider="test-arabic",
            model_version="test-only",
            synthesis_language="ar-MA",
            fallback_used=False,
        )


@pytest.fixture(autouse=True)
def inject_test_runtime() -> Iterator[None]:
    provider = InjectedSpeechProvider()
    app.dependency_overrides[get_speech_provider] = lambda: provider
    yield
    app.dependency_overrides.clear()


def test_openapi_exposes_only_core_speech_routes() -> None:
    paths = app.openapi()["paths"]
    assert set(paths) == {"/health", "/ready", "/version", "/voices", "/synthesize"}
    assert set(paths["/synthesize"]) == {"post"}


def test_health_ready_version_and_voices() -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json()["status"] == "READY"
    assert client.get("/version").json()["service"] == "speech"
    voices = client.get("/voices")
    assert voices.status_code == 200
    assert {voice["id"] for voice in voices.json()["voices"]} == {
        "darija-default",
        "arabic-fallback",
    }


def test_normalization_is_deterministic_and_controlled() -> None:
    assert normalize_darija("بغيت   الما").normalized_text == "بغيت الما"
    assert normalize_darija("3afak 3awnouni").normalized_text == "عافاك عاونوني"
    assert normalize_darija("bghit lma").normalized_text == "بغيت الما"
    assert normalize_darija("20 درهم").normalized_text == "عشرين درهم"
    assert "صفر" in normalize_darija("06 12 34 56 78").normalized_text


def test_synthesize_returns_valid_wav_through_explicit_test_injection() -> None:
    response = client.post(
        "/synthesize",
        json={
            "text": "بغيت الما",
            "language": "ar-MA",
            "voice_id": "darija-default",
            "speed": 1.0,
            "output_format": "wav",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    audio_bytes = base64.b64decode(body["audio_base64"])
    assert body["provider"] == "test-arabic"
    assert body["audio"]["mime_type"] == "audio/wav"
    assert body["audio"]["duration_ms"] > 0
    with wave.open(BytesIO(audio_bytes), "rb") as wav:
        assert wav.getframerate() == 22_050
        assert wav.getnchannels() == 1


def test_rejects_empty_too_long_or_unknown_voice() -> None:
    empty = client.post(
        "/synthesize",
        json={"text": "   ", "voice_id": "darija-default", "output_format": "wav"},
    )
    assert empty.status_code == 422
    too_long = client.post(
        "/synthesize",
        json={"text": "ا" * 501, "voice_id": "darija-default", "output_format": "wav"},
    )
    assert too_long.status_code == 422
    unknown_voice = client.post(
        "/synthesize",
        json={"text": "ما", "voice_id": "not-a-voice", "output_format": "wav"},
    )
    assert unknown_voice.status_code == 404


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/prepare"),
        ("get", "/generations/abc"),
        ("post", "/admin/reload-model"),
    ],
)
def test_removed_speech_routes_return_not_found(method: str, path: str) -> None:
    assert client.request(method, path, json={}).status_code == 404


def test_synthesis_service_rejects_work_above_its_concurrency_bound() -> None:
    service = SynthesisService(provider=InjectedSpeechProvider())
    capacity = get_settings().speech_max_concurrent_generations
    for _ in range(capacity):
        assert service._capacity.acquire(blocking=False)
    try:
        with pytest.raises(ValueError, match="SPEECH_BUSY"):
            service.synthesize(
                SynthesisRequest(
                    text="ما",
                    language="ar-MA",
                    voice_id="darija-default",
                    output_format="wav",
                )
            )
    finally:
        for _ in range(capacity):
            service._capacity.release()
