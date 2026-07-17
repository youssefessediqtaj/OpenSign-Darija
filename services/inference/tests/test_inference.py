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


def test_prediction_service_confidence_values() -> None:
    result = PredictionService().predict_mock(100)
    assert result.predictions[0].confidence > result.predictions[1].confidence
    assert result.unknown_probability == 0.03
