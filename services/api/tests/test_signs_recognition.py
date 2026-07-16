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
