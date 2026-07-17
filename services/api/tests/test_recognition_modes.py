from fastapi.testclient import TestClient

from tests.test_dataset_workflow import login
from tests.test_signs_recognition import valid_landmark_payload


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


def test_word_endpoint_preserves_existing_payload(client: TestClient) -> None:
    response = client.post("/api/v1/recognitions/word", json=valid_landmark_payload())
    assert response.status_code == 200
    assert response.json()["recognition_id"]


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
