import json

from fastapi.testclient import TestClient


def test_list_signs(client: TestClient) -> None:
    response = client.get("/api/v1/signs")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 10
    assert body["items"][0]["darija_arabic"]


def test_categories(client: TestClient) -> None:
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert {category["slug"] for category in response.json()} >= {"sante", "questions"}


def test_mock_recognition_uses_fallback_when_inference_unavailable(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions/mock", json={"source": "test", "frames_count": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["predictions"]) == 3
    assert body["predictions"][0]["rank"] == 1


def valid_landmark_payload() -> dict[str, object]:
    features = [0.1] * 63
    mask = [1] * 21
    return {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
        "captured_at": "2026-07-16T12:00:00Z",
        "duration_ms": 1600,
        "source_fps": 15.0,
        "target_frame_count": 30,
        "coordinate_format": "torso_normalized_v1",
        "feature_schema_version": "1.0.0",
        "frames": [
            {
                "index": index,
                "timestamp_ms": index * 50,
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
            "movement_score": 0.4,
        },
        "anonymous_session_id": "test-guest",
    }


def test_landmark_recognition_creates_session_without_storing_landmarks(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions", json=valid_landmark_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["recognition_id"]
    assert body["sequence_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert len(body["predictions"]) == 3
    assert "frames" not in body
    assert body["inference_mode"] == "mock"
    detail = client.get(f"/api/v1/recognitions/{body['recognition_id']}")
    assert detail.status_code == 200
    confirm = client.post(
        f"/api/v1/recognitions/{body['recognition_id']}/confirm",
        json={"prediction_id": body["predictions"][0]["prediction_id"]},
    )
    assert confirm.status_code == 200


def test_landmark_recognition_rejects_empty_sequence(client: TestClient) -> None:
    payload = valid_landmark_payload()
    payload["frames"] = []
    response = client.post(
        "/api/v1/recognitions",
        content=json.dumps(payload, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_landmark_recognition_rejects_infinite_coordinates(client: TestClient) -> None:
    payload = valid_landmark_payload()
    frames = payload["frames"]
    assert isinstance(frames, list)
    first = frames[0]
    assert isinstance(first, dict)
    first["features"] = [float("inf")] * 63
    response = client.post(
        "/api/v1/recognitions",
        content=json.dumps(payload, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_active_model_falls_back_to_mock_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/models/active")
    assert response.status_code == 200
    body = response.json()
    assert body["name"]
    assert body["feature_schema_version"] == "1.0.0"
    assert "metrics_json" in body


def test_admin_models_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/admin/models")
    assert response.status_code == 403 or response.status_code == 401
