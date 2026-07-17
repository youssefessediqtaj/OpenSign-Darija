from fastapi.testclient import TestClient

from app.main import app
from app.services.prediction_service import PredictionService

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["state"] == "READY"


def test_ready() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_version() -> None:
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_model_endpoint_is_mock() -> None:
    response = client.get("/model")
    assert response.status_code == 200
    assert response.json()["mock"] is True
    assert response.json()["feature_schema_version"] == "1.0.0"


def test_mock_prediction_format_and_top_three() -> None:
    response = client.post("/predict/mock", json={"frames_count": 42})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["inference_mode"] == "mock"
    assert body["decision"] == "known"
    assert len(body["predictions"]) == 3
    assert [item["rank"] for item in body["predictions"]] == [1, 2, 3]
    assert all(0 <= item["confidence"] <= 1 for item in body["predictions"])


def test_explicit_word_and_alphabet_routes() -> None:
    sequence = {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
        "captured_at": "2026-07-17T12:00:00Z",
        "duration_ms": 1600,
        "source_fps": 15,
        "target_frame_count": 1,
        "coordinate_format": "torso_normalized_v1",
        "feature_schema_version": "1.0.0",
        "frames": [
            {
                "index": 0,
                "timestamp_ms": 0,
                "features": [0.1] * 63,
                "presence_mask": [1] * 21,
            }
        ],
        "quality": {
            "detected_hand_ratio": 1,
            "detected_face_ratio": 1,
            "detected_pose_ratio": 1,
            "missing_frame_ratio": 0,
            "movement_score": 0.5,
        },
    }
    word = client.post("/predict/word", json=sequence)
    assert word.status_code == 200
    alphabet = client.post(
        "/predict/alphabet",
        json={
            "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
            "captured_at": "2026-07-17T12:00:00Z",
            "feature_schema_version": "1.0.0",
            "hand": "right",
            "features": [0.1] * 63,
            "presence_mask": [1] * 21,
            "stability_frames": 8,
        },
    )
    assert alphabet.status_code == 200
    assert alphabet.json()["model"]["name"] == "opensign-mosl-alphabet-mock"


def test_prediction_service_confidence_values() -> None:
    result = PredictionService().predict_mock(100)
    assert result.predictions[0].confidence > result.predictions[1].confidence
    assert result.unknown_probability == 0.03
