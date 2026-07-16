from fastapi.testclient import TestClient

CHECKSUM = "a" * 64


def login(client: TestClient, email: str, password: str = "OpenSignDemo123!") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def grant_landmark_consents(client: TestClient, headers: dict[str, str]) -> None:
    templates = client.get("/api/v1/consents/templates", headers=headers)
    assert templates.status_code == 200
    template_id = templates.json()[0]["id"]
    response = client.post(
        "/api/v1/consents",
        headers=headers,
        json={
            "consent_template_id": template_id,
            "choices": [
                {"consent_type": "LANDMARK_PROCESSING", "granted": True},
                {"consent_type": "LANDMARK_STORAGE", "granted": True},
                {"consent_type": "RESEARCH_USE", "granted": True},
                {"consent_type": "MODEL_TRAINING", "granted": True},
                {"consent_type": "VIDEO_RECORDING", "granted": False},
                {"consent_type": "VIDEO_STORAGE", "granted": False},
            ],
            "language": "fr",
            "evidence": {"test": True},
        },
    )
    assert response.status_code == 201


def recording_payload(index: int) -> dict[str, object]:
    return {
        "repetition_index": index,
        "feature_schema_version": "1.0.0",
        "duration_ms": 1800,
        "source_fps": 15,
        "target_frame_count": 30,
        "file_size_bytes": 0,
        "landmark_size_bytes": 2048,
        "checksum_landmarks": CHECKSUM,
        "quality_score": 0.9,
        "automatic_quality_status": "PASSED",
        "metrics": [
            {
                "metric_name": "detected_hand_ratio",
                "metric_value": 0.96,
                "threshold_min": 0.35,
                "passed": True,
            }
        ],
    }


def create_ready_contribution(client: TestClient, headers: dict[str, str]) -> str:
    campaigns = client.get("/api/v1/contribution-campaigns", headers=headers)
    assert campaigns.status_code == 200
    campaign_id = campaigns.json()[0]["id"]
    signs = client.get(f"/api/v1/contribution-campaigns/{campaign_id}/signs", headers=headers)
    assert signs.status_code == 200
    campaign_sign_id = signs.json()[0]["id"]
    created = client.post(
        "/api/v1/contributions",
        headers=headers,
        json={
            "campaign_id": campaign_id,
            "campaign_sign_id": campaign_sign_id,
            "wants_video": False,
        },
    )
    assert created.status_code == 201
    contribution_id = created.json()["id"]
    for index in range(1, 4):
        recording = client.post(
            f"/api/v1/contributions/{contribution_id}/recordings",
            headers=headers,
            json=recording_payload(index),
        )
        assert recording.status_code == 201
        recording_id = recording.json()["id"]
        upload = client.post(
            f"/api/v1/contributions/{contribution_id}/recordings/{recording_id}/upload-session",
            headers=headers,
            json={"include_video": False, "landmark_content_type": "application/json"},
        )
        assert upload.status_code == 200
        assert "opensign-private-landmarks" in upload.json()["landmark"]["upload_url"]
        confirmed = client.post(
            f"/api/v1/contributions/{contribution_id}/recordings/{recording_id}/confirm-upload",
            headers=headers,
            json={
                "checksum_landmarks": CHECKSUM,
                "landmark_size_bytes": 2048,
                "video_size_bytes": 0,
            },
        )
        assert confirmed.status_code == 200
    return contribution_id


def test_contribution_requires_separate_consents(client: TestClient) -> None:
    headers = login(client, "contributor@example.test")
    campaigns = client.get("/api/v1/contribution-campaigns", headers=headers).json()
    campaign_id = campaigns[0]["id"]
    campaign_sign_id = client.get(
        f"/api/v1/contribution-campaigns/{campaign_id}/signs", headers=headers
    ).json()[0]["id"]
    response = client.post(
        "/api/v1/contributions",
        headers=headers,
        json={
            "campaign_id": campaign_id,
            "campaign_sign_id": campaign_sign_id,
            "wants_video": True,
        },
    )
    assert response.status_code == 403
    assert "LANDMARK_STORAGE" in response.json()["error"]["details"]["missing"]


def test_landmark_only_contribution_review_and_dataset_build(client: TestClient) -> None:
    contributor = login(client, "contributor@example.test")
    grant_landmark_consents(client, contributor)
    contribution_id = create_ready_contribution(client, contributor)

    submitted = client.post(f"/api/v1/contributions/{contribution_id}/submit", headers=contributor)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "PENDING_LINGUIST_REVIEW"

    linguist = login(client, "linguist@example.test")
    queue = client.get("/api/v1/reviews/linguistic/queue", headers=linguist)
    assert queue.status_code == 200
    assert queue.json()[0]["id"] == contribution_id
    decision = client.post(
        f"/api/v1/reviews/linguistic/{contribution_id}/decision",
        headers=linguist,
        json={"decision": "APPROVED", "comment": "Signe conforme"},
    )
    assert decision.status_code == 200

    ml = login(client, "ml-reviewer@example.test")
    queue = client.get("/api/v1/reviews/ml/queue", headers=ml)
    assert queue.status_code == 200
    assert queue.json()[0]["id"] == contribution_id
    approved = client.post(
        f"/api/v1/reviews/ml/{contribution_id}/decision",
        headers=ml,
        json={"decision": "APPROVED", "comment": "Qualite suffisante"},
    )
    assert approved.status_code == 200

    dataset = client.post(
        "/api/v1/admin/datasets",
        headers=ml,
        json={
            "name": "opensign-darija-test",
            "semantic_version": "0.1.0",
            "description": "Test",
            "feature_schema_version": "1.0.0",
        },
    )
    assert dataset.status_code == 201
    built = client.post(f"/api/v1/admin/datasets/{dataset.json()['id']}/build", headers=ml)
    assert built.status_code == 200
    assert built.json()["recording_count"] == 3
    assert built.json()["contributor_count"] == 1


def test_horizontal_access_is_rejected(client: TestClient) -> None:
    contributor = login(client, "contributor@example.test")
    grant_landmark_consents(client, contributor)
    contribution_id = create_ready_contribution(client, contributor)

    other = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": "Other User",
            "email": "other@example.test",
            "password": "strong-password-1",
            "password_confirm": "strong-password-1",
        },
    )
    assert other.status_code == 201
    other_headers = login(client, "other@example.test", "strong-password-1")
    response = client.get(f"/api/v1/contributions/{contribution_id}", headers=other_headers)
    assert response.status_code in {403, 404}
