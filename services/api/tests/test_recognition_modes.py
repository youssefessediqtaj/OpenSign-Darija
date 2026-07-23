import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors import ApiError
from app.main import app
from app.schemas.recognition import PredictionResponse, RecognitionResponse


def valid_word_landmark_payload() -> dict[str, object]:
    frames = [
        {
            "index": index,
            "timestamp_ms": index * 33,
            "landmarks": [[0.1, 0.0, 0.0] for _ in range(75)],
            "presence_mask": [1] * 75,
        }
        for index in range(60)
    ]
    return {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174001",
        "captured_at": "2026-07-17T12:00:00Z",
        "recognition_mode": "WORD_ISOLATED",
        "duration_ms": 1600,
        "source_fps": 15,
        "target_frame_count": 60,
        "landmark_count": 75,
        "coordinate_count": 3,
        "coordinate_format": "shoulder_centered_v1",
        "feature_schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "frames": frames,
        "quality": {
            "detected_hand_ratio": 1,
            "detected_face_ratio": 0,
            "detected_pose_ratio": 1,
            "missing_frame_ratio": 0,
            "movement_score": 0.5,
        },
        "segmentation_kind": "dynamic",
        "segmentation_reliable": True,
        "usable_frame_count": 60,
    }


def fixture_word_landmark_payload() -> dict[str, object]:
    fixture_path = (
        Path(__file__).resolve().parents[3]
        / "tests/fixtures/recognition/word-recognition-v1-valid.json"
    )
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def assert_word_validation_path(response: object, expected_fragment: object) -> None:
    body = response.json()  # type: ignore[attr-defined]
    errors = body["error"]["details"]["errors"]
    paths = [error["loc"] for error in errors]
    assert any(expected_fragment in path for path in paths)


def post_word_payload(client: TestClient, payload: dict[str, object]):
    return client.post(
        "/api/v1/recognitions/word",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )


def inference_result(
    *, decision: str = "known", label_ar: str | None = "عاونّي"
) -> RecognitionResponse:
    return RecognitionResponse(
        request_id="inference-request",
        sequence_id="123e4567-e89b-12d3-a456-426614174001",
        status="completed",
        model_name="mosl-isolated-sign-v1",
        model_version="1.0.0",
        feature_schema_version="OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        inference_mode="real",
        decision=decision,
        confidence_level="high" if decision == "known" else "low",
        predictions=[
            PredictionResponse(
                label="aide",
                label_ar=label_ar,
                confidence=0.91,
                rank=1,
            )
        ],
        unknown_probability=0.09,
        processing_time_ms=3,
    )


def test_only_word_recognition_runtime_surface_is_mounted(client: TestClient) -> None:
    paths = app.openapi()["paths"]
    assert set(paths) == {
        "/health",
        "/api/v1/health",
        "/api/v1/version",
        "/api/v1/recognitions/word",
        "/api/v1/speech/sign",
    }
    assert set(paths["/api/v1/recognitions/word"]) == {"post"}
    assert set(paths["/api/v1/speech/sign"]) == {"post"}


def test_word_endpoint_uses_schema_v1_and_rejects_legacy_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    response = client.post("/api/v1/recognitions/word", json=valid_word_landmark_payload())
    assert response.status_code == 200
    assert set(response.json()) == {
        "status",
        "label_key",
        "label_ar",
        "confidence",
        "unknown",
        "latency_ms",
    }

    short_word = valid_word_landmark_payload()
    short_word["target_frame_count"] = 59
    short_word["frames"] = short_word["frames"][:59]  # type: ignore[index]
    short = client.post("/api/v1/recognitions/word", json=short_word)
    assert short.status_code == 422


def test_word_endpoint_accepts_shared_v1_fixture(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    response = client.post("/api/v1/recognitions/word", json=fixture_word_landmark_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"recognized", "unknown"}
    assert body["unknown"] is (body["status"] == "unknown")


def test_word_endpoint_returns_only_public_known_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "status": "recognized",
        "label_key": "aide",
        "label_ar": "عاونّي",
        "confidence": 0.91,
        "unknown": False,
        "latency_ms": response.json()["latency_ms"],
    }
    assert response.json()["latency_ms"] >= 0


@pytest.mark.parametrize("decision", ["unknown", "uncertain"])
def test_word_endpoint_hides_top_k_for_non_known_decisions(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, decision: str
) -> None:
    async def rejected(_: object) -> RecognitionResponse:
        return inference_result(decision=decision)

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", rejected)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unknown"
    assert body["unknown"] is True
    assert body["label_key"] is None
    assert body["label_ar"] is None
    assert "predictions" not in body


def test_word_endpoint_fails_closed_when_known_label_has_no_arabic_mapping(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def missing_mapping(_: object) -> RecognitionResponse:
        return inference_result(label_ar=None)

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", missing_mapping)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"


@pytest.mark.parametrize(
    "forbidden_field",
    ["raw_video", "image", "audio", "anonymous_session_id"],
)
def test_word_endpoint_rejects_raw_media_fields(
    client: TestClient, forbidden_field: str
) -> None:
    payload = valid_word_landmark_payload()
    payload[forbidden_field] = "data:application/octet-stream;base64,AAAA"
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 422
    assert_word_validation_path(response, forbidden_field)


@pytest.mark.parametrize("container", ["frame", "quality"])
def test_word_endpoint_rejects_nested_extra_fields(client: TestClient, container: str) -> None:
    payload = valid_word_landmark_payload()
    if container == "frame":
        payload["frames"][0]["pixels"] = [1, 2, 3]  # type: ignore[index]
        expected = "pixels"
    else:
        payload["quality"]["raw_confidence"] = 0.9  # type: ignore[index]
        expected = "raw_confidence"
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 422
    assert_word_validation_path(response, expected)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update(duration_ms=100),
        lambda payload: payload.update(segmentation_reliable=False),
        lambda payload: payload.update(usable_frame_count=5),
        lambda payload: payload["quality"].update(detected_hand_ratio=0.1),
        lambda payload: payload["quality"].update(detected_pose_ratio=0.1),
        lambda payload: payload["quality"].update(missing_frame_ratio=0.8),
        lambda payload: payload["quality"].update(movement_score=0.0),
        lambda payload: [frame.update(presence_mask=[0] * 75) for frame in payload["frames"]],
    ],
)
def test_semantically_unusable_sequences_return_unknown_without_inference(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    mutator: Callable[[dict[str, object]], object],
) -> None:
    async def must_not_run(_: object) -> RecognitionResponse:
        raise AssertionError("inference must not run for unusable captures")

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", must_not_run)
    payload = valid_word_landmark_payload()
    mutator(payload)
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"
    assert response.json()["confidence"] == 0


def test_reliable_static_sign_can_have_low_movement(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    payload = valid_word_landmark_payload()
    payload["segmentation_kind"] = "static"
    payload["quality"]["movement_score"] = 0.0  # type: ignore[index]
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "recognized"


def test_word_endpoint_propagates_model_unavailability(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable(_: object) -> RecognitionResponse:
        raise ApiError("INFERENCE_MODEL_UNAVAILABLE", "unavailable", 503)

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", unavailable)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INFERENCE_MODEL_UNAVAILABLE"


def test_word_endpoint_has_no_transport_error_prediction_fallback(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail_post(
        _: httpx.AsyncClient, url: str, **__: object
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "test-only transport failure",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fail_post)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INFERENCE_UNAVAILABLE"


def test_word_endpoint_rejects_mock_or_malformed_upstream_results(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_post(
        _: httpx.AsyncClient, url: str, **__: object
    ) -> httpx.Response:
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "request_id": "mock-request",
                "sequence_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "completed",
                "model": {"name": "mock-model", "version": "0.0.0"},
                "feature_schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                "inference_mode": "mock",
                "decision": "known",
                "confidence_level": "high",
                "predictions": [
                    {"label": "invented", "label_ar": "وهمي", "confidence": 0.99, "rank": 1}
                ],
                "unknown_probability": 0.01,
                "processing_time_ms": 1,
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "INFERENCE_UNAVAILABLE"


def test_word_endpoint_is_database_independent(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    payload = valid_word_landmark_payload()
    response = client.post("/api/v1/recognitions/word", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "recognized"


def test_core_app_import_graph_excludes_stateful_infrastructure() -> None:
    command = """
import sys
from app.main import app
blocked = {
    'app.db',
    'app.api.v1.messages',
    'app.services.object_storage',
    'app.models',
    'redis',
    'minio',
    'sqlalchemy',
}
loaded = {
    name
    for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
}
assert not loaded, loaded
assert set(app.openapi()['paths']) == {
    '/health',
    '/api/v1/health',
    '/api/v1/version',
    '/api/v1/recognitions/word',
    '/api/v1/speech/sign',
}
"""
    environment = {
        **os.environ,
        "DATABASE_URL": "postgresql+psycopg://unused:unused@127.0.0.1:1/unused",
        "REDIS_URL": "redis://127.0.0.1:1/0",
        "MINIO_ENDPOINT": "127.0.0.1:1",
    }
    result = subprocess.run(
        [sys.executable, "-c", command],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_word_endpoint_rate_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.api.v1.recognitions import rate_limit_bucket

    async def recognized(_: object) -> RecognitionResponse:
        return inference_result()

    monkeypatch.setattr("app.api.v1.recognitions.predict_sequence", recognized)
    monkeypatch.setenv("RECOGNITION_RATE_LIMIT", "1")
    get_settings.cache_clear()
    rate_limit_bucket.clear()
    payload = valid_word_landmark_payload()
    try:
        first = client.post("/api/v1/recognitions/word", json=payload)
        second = client.post("/api/v1/recognitions/word", json=payload)
    finally:
        rate_limit_bucket.clear()
        get_settings.cache_clear()
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMITED"


@pytest.mark.parametrize(
    ("mutator", "field"),
    [
        (lambda payload: payload.update(sequence_id="not-a-uuid"), "sequence_id"),
        (lambda payload: payload.update(frames=[]), "frames"),
        (lambda payload: payload.update(frames=payload["frames"][:59]), "frames"),
        (
            lambda payload: payload.update(
                frames=payload["frames"] + [payload["frames"][-1]]
            ),
            "frames",
        ),
        (
            lambda payload: payload["frames"][0].update(
                landmarks=payload["frames"][0]["landmarks"][:74]
            ),
            "landmarks",
        ),
        (
            lambda payload: payload["frames"][0].update(
                landmarks=payload["frames"][0]["landmarks"]
                + [payload["frames"][0]["landmarks"][-1]]
            ),
            "landmarks",
        ),
        (lambda payload: payload["frames"][0]["landmarks"][0].pop(), 0),
        (lambda payload: payload["frames"][0]["landmarks"][0].append(0.4), 0),
        (lambda payload: payload["frames"][0]["landmarks"][0].__setitem__(0, float("nan")), 0),
        (lambda payload: payload["frames"][0]["landmarks"][0].__setitem__(0, float("inf")), 0),
        (lambda payload: payload.update(feature_schema_version="1.0.0"), "feature_schema_version"),
        (lambda payload: payload.update(recognition_mode="ALPHABET_STATIC"), "recognition_mode"),
        (lambda payload: payload["frames"][0].update(timestamp_ms=16000), "timestamp_ms"),
    ],
)
def test_word_endpoint_rejects_invalid_v1_payloads(
    client: TestClient, mutator: Callable[[dict[str, object]], object], field: object
) -> None:
    payload = fixture_word_landmark_payload()
    mutator(payload)
    response = post_word_payload(client, payload)
    assert response.status_code == 422
    assert_word_validation_path(response, field)


def test_word_endpoint_rejects_oversized_request(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RECOGNITION_MAX_PAYLOAD_BYTES", "100")
    get_settings.cache_clear()
    try:
        response = client.post("/api/v1/recognitions/word", json=fixture_word_landmark_payload())
    finally:
        get_settings.cache_clear()
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
