import base64
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors import ApiError


def write_checksums(package_dir: Path) -> None:
    manifest = {
        filename: hashlib.sha256((package_dir / filename).read_bytes()).hexdigest()
        for filename in ("labels.json", "supported-signs.json")
    }
    (package_dir / "checksums.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_verified_catalog(package_dir: Path) -> Path:
    package_dir.mkdir()
    (package_dir / "labels.json").write_text(
        json.dumps(["help", "thanks"]),
        encoding="utf-8",
    )
    catalog_path = package_dir / "supported-signs.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_SUPPORTED_SIGNS_V1",
                "model_name": "test-real-model",
                "vocabulary_size": 2,
                "signs": [
                    {
                        "label_key": "help",
                        "label_ar": "عاونّي",
                        "status": "SUPPORTED_FOR_TRAINING",
                    },
                    {
                        "label_key": "thanks",
                        "label_ar": "شكرا",
                        "status": "SUPPORTED_FOR_TRAINING",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_checksums(package_dir)
    return catalog_path


@pytest.fixture(autouse=True)
def verified_model_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Path]:
    catalog_path = write_verified_catalog(tmp_path / "model-package")
    monkeypatch.setenv("SUPPORTED_SIGNS_PATH", str(catalog_path))
    get_settings.cache_clear()
    yield catalog_path
    get_settings.cache_clear()


def fake_synthesize(
    text: str, language: str, voice_id: str, speed: float, output_format: str
) -> dict[str, object]:
    audio = b"RIFF-test-wav"
    return {
        "generation_id": "speech-service-id",
        "status": "completed",
        "requested_language": language,
        "synthesis_language": "ar-MA" if voice_id == "darija-default" else "ar",
        "fallback_used": voice_id != "darija-default",
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "audio": {
            "mime_type": "audio/wav",
            "duration_ms": 100,
            "file_size_bytes": len(audio),
        },
    }


def test_direct_sign_speech_resolves_arabic_and_returns_playable_audio(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.clients.speech import SpeechServiceClient

    calls: list[dict[str, object]] = []

    def synthesize(self, **kwargs):
        calls.append(kwargs)
        return fake_synthesize(**kwargs)

    monkeypatch.setattr(SpeechServiceClient, "synthesize", synthesize)
    response = client.post("/api/v1/speech/sign", json={"label_key": "help"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["label_key"] == "help"
    assert body["label_ar"] == "عاونّي"
    assert body["audio"]["url"].startswith("data:audio/wav;base64,")
    assert calls == [
        {
            "text": "عاونّي",
            "language": "ar-MA",
            "voice_id": "darija-default",
            "speed": 1.0,
            "output_format": "wav",
        }
    ]


def test_direct_sign_speech_rejects_unsupported_or_user_supplied_text(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.clients.speech import SpeechServiceClient

    def must_not_run(self, **kwargs):
        raise AssertionError("unsupported signs must not reach speech synthesis")

    monkeypatch.setattr(SpeechServiceClient, "synthesize", must_not_run)
    unsupported = client.post("/api/v1/speech/sign", json={"label_key": "not-supported"})
    assert unsupported.status_code == 404
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_SIGN"
    injected = client.post(
        "/api/v1/speech/sign",
        json={"label_key": "help", "text": "arbitrary user text"},
    )
    assert injected.status_code == 422


def test_direct_sign_speech_falls_back_from_moroccan_arabic_to_arabic(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.clients.speech import SpeechServiceClient

    calls: list[tuple[str, str]] = []

    def synthesize(self, **kwargs):
        calls.append((str(kwargs["language"]), str(kwargs["voice_id"])))
        if kwargs["language"] == "ar-MA":
            raise ApiError("SPEECH_GENERATION_FAILED", "primary failed", 422)
        return fake_synthesize(**kwargs)

    monkeypatch.setattr(SpeechServiceClient, "synthesize", synthesize)
    response = client.post("/api/v1/speech/sign", json={"label_key": "thanks"})
    assert response.status_code == 200
    assert response.json()["fallback_used"] is True
    assert calls == [("ar-MA", "darija-default"), ("ar", "arabic-fallback")]


def test_direct_sign_speech_failure_is_a_separate_request_failure(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.clients.speech import SpeechServiceClient

    def fail(self, **kwargs):
        raise ApiError("SPEECH_SERVICE_UNAVAILABLE", "speech unavailable", 503)

    monkeypatch.setattr(SpeechServiceClient, "synthesize", fail)
    response = client.post("/api/v1/speech/sign", json={"label_key": "help"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SPEECH_SERVICE_UNAVAILABLE"


def test_direct_sign_speech_rejects_invalid_upstream_audio(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.clients.speech import SpeechServiceClient

    monkeypatch.setattr(SpeechServiceClient, "synthesize", lambda self, **kwargs: {})
    response = client.post("/api/v1/speech/sign", json={"label_key": "help"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "SPEECH_GENERATION_FAILED"


def test_direct_sign_speech_fails_closed_without_a_local_catalog(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.clients.speech import SpeechServiceClient

    monkeypatch.setenv("SUPPORTED_SIGNS_PATH", str(tmp_path / "missing.json"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        SpeechServiceClient,
        "synthesize",
        lambda self, **kwargs: pytest.fail("speech must not run without a verified catalog"),
    )
    response = client.post("/api/v1/speech/sign", json={"label_key": "help"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SUPPORTED_SIGNS_UNAVAILABLE"


def test_direct_sign_speech_rejects_catalog_checksum_tampering(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    verified_model_package: Path,
) -> None:
    from app.clients.speech import SpeechServiceClient

    verified_model_package.write_text(
        verified_model_package.read_text(encoding="utf-8").replace("عاونّي", "نص مزور"),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        SpeechServiceClient,
        "synthesize",
        lambda self, **kwargs: pytest.fail("speech must not run with a tampered catalog"),
    )
    response = client.post("/api/v1/speech/sign", json={"label_key": "help"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SUPPORTED_SIGNS_INVALID"
