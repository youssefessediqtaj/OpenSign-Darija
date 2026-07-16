from fastapi.testclient import TestClient


def register_payload(email: str = "demo@example.com") -> dict[str, str]:
    return {
        "display_name": "Demo User",
        "email": email,
        "password": "strong-password-1",
        "password_confirm": "strong-password-1",
    }


def test_register_assigns_user_role(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=register_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "demo@example.com"
    assert body["roles"] == ["USER"]


def test_login_and_me(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=register_payload())
    login = client.post(
        "/api/v1/auth/login", json={"email": "demo@example.com", "password": "strong-password-1"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "demo@example.com"


def test_invalid_password(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=register_payload())
    response = client.post(
        "/api/v1/auth/login", json={"email": "demo@example.com", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
