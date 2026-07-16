from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def valid_payload(sequence_id: str | None = None) -> dict[str, object]:
    features = [0.1] * 63
    mask = [1] * 21
    return {
        "sequence_id": sequence_id or str(uuid4()),
        "captured_at": "2026-07-16T12:00:00Z",
        "duration_ms": 1800,
        "source_fps": 15.0,
        "target_frame_count": 30,
        "coordinate_format": "torso_normalized_v1",
        "feature_schema_version": "1.0.0",
        "frames": [
            {
                "index": index,
                "timestamp_ms": index * 60,
                "features": features,
                "presence_mask": mask,
            }
            for index in range(30)
        ],
        "quality": {
            "detected_hand_ratio": 0.9,
            "detected_face_ratio": 1.0,
            "detected_pose_ratio": 1.0,
            "missing_frame_ratio": 0.0,
            "movement_score": 0.5,
        },
    }


def test_predict_sequence_is_deterministic() -> None:
    sequence_id = str(uuid4())
    first = client.post("/predict", json=valid_payload(sequence_id))
    second = client.post("/predict", json=valid_payload(sequence_id))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["predictions"] == second.json()["predictions"]


def test_predict_sequence_top_three_and_schema_version() -> None:
    response = client.post("/predict", json=valid_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["model"]["version"] == "0.2.0"
    assert body["feature_schema_version"] == "1.0.0"
    assert [item["rank"] for item in body["predictions"]] == [1, 2, 3]
    assert (
        sum(item["confidence"] for item in body["predictions"]) + body["unknown_probability"]
        <= 1.05
    )


def test_predict_sequence_rejects_invalid_payload() -> None:
    payload = valid_payload()
    payload["frames"] = []
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
