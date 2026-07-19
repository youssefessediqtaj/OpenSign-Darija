import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.enums import InputModality, ModelStatus, RecognitionTaskType
from app.models.sign import ModelVersion
from tests.test_dataset_workflow import login
from tests.test_signs_recognition import valid_landmark_payload


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
        "anonymous_session_id": "test-guest",
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


def test_recognition_modes_and_task_models(client: TestClient) -> None:
    modes = client.get("/api/v1/recognition-modes")
    assert modes.status_code == 200
    assert {item["task_type"] for item in modes.json()} == {"WORD_ISOLATED", "ALPHABET_STATIC"}

    alphabet = client.get("/api/v1/models/active?task_type=ALPHABET_STATIC")
    assert alphabet.status_code == 200
    assert alphabet.json()["task_type"] == "ALPHABET_STATIC"
    assert alphabet.json()["is_active"] is False

    word = client.get("/api/v1/models/active?task_type=WORD_ISOLATED")
    assert word.status_code == 200
    assert word.json()["task_type"] == "WORD_ISOLATED"


def test_legacy_payload_still_works_on_compatibility_route(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions", json=valid_landmark_payload())
    assert response.status_code == 200
    assert response.json()["recognition_id"]


def test_word_endpoint_uses_schema_v1_and_rejects_legacy_payload(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions/word", json=valid_word_landmark_payload())
    assert response.status_code == 200
    assert response.json()["feature_schema_version"] == "OPEN_SIGNE_LANDMARK_SCHEMA_V1"

    legacy = client.post("/api/v1/recognitions/word", json=valid_landmark_payload())
    assert legacy.status_code == 422

    short_word = valid_word_landmark_payload()
    short_word["target_frame_count"] = 59
    short_word["frames"] = short_word["frames"][:59]  # type: ignore[index]
    short = client.post("/api/v1/recognitions/word", json=short_word)
    assert short.status_code == 422


def test_word_endpoint_accepts_shared_v1_fixture(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions/word", json=fixture_word_landmark_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["feature_schema_version"] == "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
    assert body["sequence_id"] == "123e4567-e89b-42d3-a456-426614174001"


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


def test_alphabet_endpoint_rejects_bad_features(client: TestClient) -> None:
    payload = {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
        "captured_at": "2026-07-17T12:00:00Z",
        "feature_schema_version": "1.0.0",
        "hand": "right",
        "features": [0.1] * 10,
        "presence_mask": [1] * 21,
        "stability_frames": 8,
    }
    response = client.post("/api/v1/recognitions/alphabet", json=payload)
    assert response.status_code == 422


def test_admin_external_datasets_and_license_gate(client: TestClient) -> None:
    headers = login(client, "ml-reviewer@example.test")
    response = client.get("/api/v1/admin/external-datasets", headers=headers)
    assert response.status_code == 200
    by_code = {item["code"]: item for item in response.json()}
    assert by_code["mendeley_mosl_v1"]["license_status"] == "VERIFIED"
    assert by_code["kaggle_moroccan_lsm_alphabet"]["license_status"] == "TO_VERIFY"

    validate = client.post(
        "/api/v1/admin/external-datasets/kaggle_moroccan_lsm_alphabet/validate",
        headers=headers,
    )
    assert validate.status_code == 409
    assert validate.json()["error"]["code"] == "LICENSE_NOT_VERIFIED"


def test_smoke_model_activation_requires_development_flag(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = login(client, "ml-reviewer@example.test")
    with SessionLocal() as db:
        model = ModelVersion(
            name="mosl-word-smoke-v1",
            semantic_version="0.1.0-smoke",
            status=ModelStatus.VALIDATED_SMOKE,
            task_type=RecognitionTaskType.WORD_ISOLATED,
            input_modality=InputModality.LANDMARK_SEQUENCE,
            architecture="bidirectional-gru",
            vocabulary_size=2,
            description="Smoke model for dev validation.",
            labels_json=["16", "17"],
            metrics_json={"production_ready": False},
            artifact_path="/tmp/mosl-word-smoke-v1",
            checksum="b" * 64,
            size_bytes=1,
            feature_schema_version="OPEN_SIGNE_LANDMARK_SCHEMA_V1",
            supported_classes=["16", "17"],
        )
        db.add(model)
        db.commit()
        model_id = model.id

    rejected = client.post(f"/api/v1/admin/models/{model_id}/activate", headers=headers)
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "MODEL_NOT_READY"

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_SMOKE_MODEL_ACTIVATION", "true")
    get_settings.cache_clear()
    activated = client.post(f"/api/v1/admin/models/{model_id}/activate", headers=headers)
    get_settings.cache_clear()

    assert activated.status_code == 200
    body = activated.json()
    assert body["status"] == "VALIDATED_SMOKE"
    assert body["is_active"] is True
    active = client.get("/api/v1/models/active?task_type=WORD_ISOLATED")
    assert active.status_code == 200
    assert active.json()["name"] == "mosl-word-smoke-v1"
    assert active.json()["status"] == "VALIDATED_SMOKE"
