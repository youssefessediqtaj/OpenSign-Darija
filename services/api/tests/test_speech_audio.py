import base64
import hashlib
import io
import wave

from fastapi.testclient import TestClient

from tests.test_messages_linguistics import ANON, add_sign, create_guest_message


def wav_payload() -> tuple[str, dict[str, object]]:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(22050)
        wav.writeframes(b"\x01\x00" * 2205)
    audio = output.getvalue()
    return base64.b64encode(audio).decode("ascii"), {
        "mime_type": "audio/wav",
        "extension": "wav",
        "sample_rate": 22050,
        "channels": 1,
        "duration_ms": 100,
        "file_size_bytes": len(audio),
        "checksum": hashlib.sha256(audio).hexdigest(),
    }


def fake_synthesize(
    text: str, language: str, voice_id: str, speed: float, output_format: str
) -> dict[str, object]:
    audio_base64, audio = wav_payload()
    normalized = " ".join(text.split())
    return {
        "generation_id": "speech-service-id",
        "status": "completed",
        "provider": "local-darija" if voice_id == "darija-default" else "local-arabic-fallback",
        "model_version": "opensign-tone-v1",
        "requested_language": language,
        "synthesis_language": "ary-MA" if voice_id == "darija-default" else "ar",
        "fallback_used": voice_id != "darija-default",
        "original_text_hash": hashlib.sha256(text.encode()).hexdigest(),
        "normalized_text_hash": hashlib.sha256(normalized.encode()).hexdigest(),
        "normalized_text": normalized,
        "normalization_version": "darija-normalizer-1.0.0",
        "audio_base64": audio_base64,
        "audio": audio,
    }


def finalized_water_message(client: TestClient) -> str:
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "WANT", "speech-want")
    add_sign(client, message_id, "WATER", "speech-water")
    generated = client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert generated.status_code == 200
    finalized = client.post(
        f"/api/v1/messages/{message_id}/finalize",
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert finalized.status_code == 200
    return message_id


def test_speech_voices_and_status(client: TestClient) -> None:
    voices = client.get("/api/v1/speech/voices")
    assert voices.status_code == 200
    assert {voice["id"] for voice in voices.json()["voices"]} >= {"darija-default"}
    status = client.get("/api/v1/speech/status")
    assert status.status_code == 200
    assert status.json()["browser_fallback_enabled"] is True


def test_generate_speech_for_finalized_message(client: TestClient, monkeypatch) -> None:
    from app.services.speech.client import SpeechServiceClient

    monkeypatch.setattr(
        SpeechServiceClient,
        "synthesize",
        lambda self, *args, **kwargs: fake_synthesize(*args, **kwargs),
    )
    message_id = finalized_water_message(client)
    response = client.post(
        f"/api/v1/messages/{message_id}/speech",
        json={"voice_id": "darija-default", "speed": 1, "format": "wav"},
        headers={"X-Anonymous-Session-Id": ANON, "Idempotency-Key": "speak-1"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["audio"]["mime_type"] == "audio/wav"
    assert "بغيت" not in body["audio"]["url"]
    second = client.post(
        f"/api/v1/messages/{message_id}/speech",
        json={"voice_id": "darija-default", "speed": 1, "format": "wav"},
        headers={"X-Anonymous-Session-Id": ANON, "Idempotency-Key": "speak-1"},
    )
    assert second.status_code == 200
    assert second.json()["generation_id"] == body["generation_id"]


def test_speech_cache_hit_for_same_message(client: TestClient, monkeypatch) -> None:
    from app.services.speech.client import SpeechServiceClient

    calls = {"count": 0}

    def counted(self, *args, **kwargs):
        calls["count"] += 1
        return fake_synthesize(*args, **kwargs)

    monkeypatch.setattr(SpeechServiceClient, "synthesize", counted)
    message_id = finalized_water_message(client)
    headers = {"X-Anonymous-Session-Id": ANON}
    first = client.post(f"/api/v1/messages/{message_id}/speech", json={}, headers=headers)
    second = client.post(f"/api/v1/messages/{message_id}/speech", json={}, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cache_hit"] is True
    assert calls["count"] == 1


def test_sensitive_message_requires_confirmation(client: TestClient, monkeypatch) -> None:
    from app.services.speech.client import SpeechServiceClient

    monkeypatch.setattr(
        SpeechServiceClient,
        "synthesize",
        lambda self, *args, **kwargs: fake_synthesize(*args, **kwargs),
    )
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "EMERGENCY", "speech-emergency")
    client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    client.post(f"/api/v1/messages/{message_id}/finalize", headers={"X-Anonymous-Session-Id": ANON})
    rejected = client.post(
        f"/api/v1/messages/{message_id}/speech",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert rejected.status_code == 409
    accepted = client.post(
        f"/api/v1/messages/{message_id}/speech",
        json={"sensitive_confirmed": True},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert accepted.status_code == 200


def test_speech_generation_requires_matching_guest_session(client: TestClient) -> None:
    message_id = finalized_water_message(client)
    response = client.post(
        f"/api/v1/messages/{message_id}/speech",
        json={},
        headers={"X-Anonymous-Session-Id": "other-session"},
    )
    assert response.status_code == 403
