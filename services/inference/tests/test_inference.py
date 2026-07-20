from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.prediction import PredictionItem, WordLandmarkSequenceRequest
from app.services.model_loader import model_loader

client = TestClient(app)


class FakeRuntimeModel:
    def predict(
        self,
        payload: WordLandmarkSequenceRequest,
    ) -> tuple[list[PredictionItem], str, str, float]:
        assert len(payload.frames) == 60
        return (
            [
                PredictionItem(label="help", label_ar="عاونّي", confidence=0.91, rank=1),
                PredictionItem(label="water", label_ar="ما", confidence=0.06, rank=2),
            ],
            "known",
            "high",
            0.09,
        )


@pytest.fixture(autouse=True)
def restore_model_loader(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    original_model = model_loader.model
    original_state = model_loader.state
    original_error = model_loader.error
    yield
    monkeypatch.setattr(model_loader, "model", original_model)
    monkeypatch.setattr(model_loader, "state", original_state)
    monkeypatch.setattr(model_loader, "error", original_error)


def valid_word_payload() -> dict[str, object]:
    return {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
        "captured_at": "2026-07-17T12:00:00Z",
        "recognition_mode": "WORD_ISOLATED",
        "duration_ms": 1600,
        "source_fps": 15,
        "target_frame_count": 60,
        "landmark_count": 75,
        "coordinate_count": 3,
        "coordinate_format": "shoulder_centered_v1",
        "feature_schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "frames": [
            {
                "index": index,
                "timestamp_ms": index * 33,
                "landmarks": [[0.1, 0.0, 0.0] for _ in range(75)],
                "presence_mask": [1] * 75,
            }
            for index in range(60)
        ],
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


def test_openapi_exposes_only_core_inference_routes() -> None:
    paths = app.openapi()["paths"]
    assert set(paths) == {"/health", "/ready", "/version", "/model", "/predict/word"}
    assert set(paths["/predict/word"]) == {"post"}


def test_runtime_fails_closed_without_a_loaded_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_loader, "model", None)
    monkeypatch.setattr(model_loader, "state", "MODEL_NOT_FOUND")
    monkeypatch.setattr(model_loader, "error", "MODEL_PATH is required")

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["state"] == "MODEL_NOT_FOUND"

    ready = client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["detail"]["state"] == "MODEL_NOT_FOUND"

    prediction = client.post("/predict/word", json=valid_word_payload())
    assert prediction.status_code == 503
    assert prediction.json()["detail"] == "MODEL_PATH is required"


def test_version_and_real_model_metadata() -> None:
    assert client.get("/version").json()["version"] == "0.1.0"
    body = client.get("/model").json()
    assert body["name"] == "mosl-isolated-sign-v1"
    assert body["version"] == "1.0.0"
    assert body["mock"] is False
    assert body["feature_schema_version"] == "OPEN_SIGNE_LANDMARK_SCHEMA_V1"


def test_word_prediction_uses_explicit_runtime_injection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(model_loader, "model", FakeRuntimeModel())
    monkeypatch.setattr(model_loader, "state", "READY")
    monkeypatch.setattr(model_loader, "error", None)

    response = client.post("/predict/word", json=valid_word_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["inference_mode"] == "real"
    assert body["feature_schema_version"] == "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
    assert body["decision"] == "known"
    assert body["predictions"][0]["label_ar"] == "عاونّي"
    assert [item["rank"] for item in body["predictions"]] == [1, 2]


@pytest.mark.parametrize(
    "path",
    ["/predict", "/predict/mock", "/predict/alphabet", "/admin/reload-model"],
)
def test_removed_inference_routes_return_not_found(path: str) -> None:
    assert client.post(path, json={}).status_code == 404


@pytest.mark.parametrize("extra_field", ["raw_video", "image", "audio"])
def test_word_route_rejects_raw_media(extra_field: str) -> None:
    payload = valid_word_payload()
    payload[extra_field] = "forbidden"
    assert client.post("/predict/word", json=payload).status_code == 422
