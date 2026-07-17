from fastapi.testclient import TestClient

from tests.test_signs_recognition import valid_landmark_payload

ANON = "guest-message-test"


def sign_id(client: TestClient, code: str) -> str:
    response = client.get("/api/v1/signs")
    assert response.status_code == 200
    for item in response.json()["items"]:
        if item["code"] == code:
            return item["id"]
    raise AssertionError(f"missing sign {code}")


def create_guest_message(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/messages",
        json={"anonymous_session_id": ANON, "title": "Test"},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert response.status_code == 200, response.text
    return response.json()


def add_sign(client: TestClient, message_id: str, code: str, key: str) -> dict[str, object]:
    response = client.post(
        f"/api/v1/messages/{message_id}/items",
        json={"sign_id": sign_id(client, code), "idempotency_key": key},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_linguistic_dictionary_and_version_are_available(client: TestClient) -> None:
    version = client.get("/api/v1/linguistics/version")
    assert version.status_code == 200
    assert version.json()["engine_mode"] == "controlled"
    concepts = client.get("/api/v1/linguistics/concepts")
    assert concepts.status_code == 200
    codes = {item["code"] for item in concepts.json()}
    assert {"ACTION_WANT", "OBJECT_WATER", "REQUEST_HELP"} <= codes
    templates = client.get("/api/v1/linguistics/templates")
    assert templates.status_code == 200
    assert {item["code"] for item in templates.json()} >= {"WANT_OBJECT", "REQUEST_HELP"}


def test_want_water_generates_darija_without_extra_politeness(client: TestClient) -> None:
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "WANT", "want-1")
    add_sign(client, message_id, "WATER", "water-1")
    generated = client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={"idempotency_key": "gen-1"},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert generated.status_code == 200, generated.text
    body = generated.json()
    assert body["linguistic_status"] == "HIGH"
    assert body["semantic_sequence"] == ["ACTION_WANT", "OBJECT_WATER"]
    assert body["result"]["darija_arabic"] == "بغيت الما"
    assert body["result"]["darija_latin"] == "bghit lma"
    assert "عافاك" not in body["result"]["darija_arabic"]
    assert body["system_insertions"] == []


def test_incomplete_want_does_not_invent_object(client: TestClient) -> None:
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "WANT", "want-only")
    generated = client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert generated.status_code == 200
    body = generated.json()
    assert body["linguistic_status"] == "INCOMPLETE"
    assert "OBJECT" in body["warnings"][0]
    assert body["result"]["darija_arabic"] == "بغيت"


def test_where_doctor_returns_ambiguous_alternatives(client: TestClient) -> None:
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "DOCTOR", "doctor-1")
    add_sign(client, message_id, "WHERE", "where-1")
    generated = client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert generated.status_code == 200
    body = generated.json()
    assert body["linguistic_status"] == "AMBIGUOUS"
    assert len(body["alternatives"]) == 2
    assert "الطبيب" in body["result"]["darija_arabic"]


def test_recognition_must_be_confirmed_before_message_add(client: TestClient) -> None:
    message = create_guest_message(client)
    recognition = client.post("/api/v1/recognitions", json=valid_landmark_payload())
    assert recognition.status_code == 200
    recognition_body = recognition.json()
    rejected = client.post(
        f"/api/v1/messages/{message['id']}/items",
        json={"recognition_session_id": recognition_body["recognition_id"]},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert rejected.status_code == 422
    confirm = client.post(
        f"/api/v1/recognitions/{recognition_body['recognition_id']}/confirm",
        json={"prediction_id": recognition_body["predictions"][0]["prediction_id"]},
    )
    assert confirm.status_code == 200
    added = client.post(
        f"/api/v1/messages/{message['id']}/items",
        json={
            "recognition_session_id": recognition_body["recognition_id"],
            "idempotency_key": "recognition-add-1",
        },
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert added.status_code == 200, added.text
    assert added.json()["item_count"] == 1
    duplicate = client.post(
        f"/api/v1/messages/{message['id']}/items",
        json={
            "recognition_session_id": recognition_body["recognition_id"],
            "idempotency_key": "recognition-add-1",
        },
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["item_count"] == 1


def test_manual_edit_preserves_generated_text_and_history(client: TestClient) -> None:
    message = create_guest_message(client)
    message_id = str(message["id"])
    add_sign(client, message_id, "HELP", "help-1")
    generated = client.post(
        f"/api/v1/messages/{message_id}/generate",
        json={},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert generated.status_code == 200
    updated = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"final_darija_arabic": "عاونوني دابا"},
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["generated_darija_arabic"] == "عاونوني"
    assert body["final_darija_arabic"] == "عاونوني دابا"
    finalized = client.post(
        f"/api/v1/messages/{message_id}/finalize",
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert finalized.status_code == 200
    favorite = client.post(
        f"/api/v1/messages/{message_id}/favorite",
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert favorite.status_code == 200
    assert favorite.json()["is_favorite"] is True
    history = client.get("/api/v1/messages", headers={"X-Anonymous-Session-Id": ANON})
    assert history.status_code == 200
    assert history.json()["total"] >= 1
    revisions = client.get(
        f"/api/v1/messages/{message_id}/revisions",
        headers={"X-Anonymous-Session-Id": ANON},
    )
    assert revisions.status_code == 200
    assert {item["change_type"] for item in revisions.json()} >= {"GENERATED", "FINALIZED"}


def test_message_access_requires_matching_guest_session(client: TestClient) -> None:
    message = create_guest_message(client)
    response = client.get(
        f"/api/v1/messages/{message['id']}",
        headers={"X-Anonymous-Session-Id": "other-session"},
    )
    assert response.status_code == 403
