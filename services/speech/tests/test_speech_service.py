import base64
import wave
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.preprocessing.darija_normalizer import normalize_darija


client = TestClient(app)


def test_health_ready_and_voices() -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json()["status"] == "READY"
    voices = client.get("/voices")
    assert voices.status_code == 200
    assert {voice["id"] for voice in voices.json()["voices"]} >= {
        "darija-default",
        "arabic-fallback",
    }


def test_normalization_is_deterministic_and_controlled() -> None:
    assert normalize_darija("بغيت   الما").normalized_text == "بغيت الما"
    assert normalize_darija("3afak 3awnouni").normalized_text == "عافاك عاونوني"
    assert normalize_darija("bghit lma").normalized_text == "بغيت الما"
    assert normalize_darija("20 درهم").normalized_text == "عشرين درهم"
    assert "صفر" in normalize_darija("06 12 34 56 78").normalized_text


def test_synthesize_returns_valid_wav() -> None:
    response = client.post(
        "/synthesize",
        json={
            "text": "بغيت الما",
            "language": "ary-MA",
            "voice_id": "darija-default",
            "speed": 1.0,
            "output_format": "wav",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    audio_bytes = base64.b64decode(body["audio_base64"])
    assert body["audio"]["mime_type"] == "audio/wav"
    assert body["audio"]["duration_ms"] > 0
    with wave.open(BytesIO(audio_bytes), "rb") as wav:
        assert wav.getframerate() == 22050
        assert wav.getnchannels() == 1


def test_rejects_empty_or_too_long_text() -> None:
    empty = client.post(
        "/synthesize",
        json={"text": "   ", "voice_id": "darija-default", "speed": 1, "output_format": "wav"},
    )
    assert empty.status_code == 422
    too_long = client.post(
        "/synthesize",
        json={"text": "ا" * 501, "voice_id": "darija-default", "speed": 1, "output_format": "wav"},
    )
    assert too_long.status_code == 422
