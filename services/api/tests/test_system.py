from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_health_checks_only_required_stateless_services(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def healthy(url: str, timeout_seconds: float) -> str:
        assert timeout_seconds > 0
        assert url.endswith("/health")
        return "healthy"

    monkeypatch.setattr("app.api.v1.system.service_health", healthy)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "opensign-api",
        "version": get_settings().app_version,
        "dependencies": {"inference": "healthy", "speech": "healthy"},
    }
    assert client.get("/health").json() == response.json()


def test_health_degrades_without_blocking_boot(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable(url: str, timeout_seconds: float) -> str:
        return "unhealthy"

    monkeypatch.setattr("app.api.v1.system.service_health", unavailable)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"] == {
        "inference": "unhealthy",
        "speech": "unhealthy",
    }


def test_version(client: TestClient) -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json() == {
        "service": "opensign-api",
        "version": get_settings().app_version,
    }


def test_docker_command_starts_api_without_migration_or_seed() -> None:
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")
    command = dockerfile.splitlines()[-1]
    assert command == (
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", '
        '"--proxy-headers", "--forwarded-allow-ips=*"]'
    )
    assert "alembic" not in command
    assert "seed" not in command


def test_nginx_is_the_only_public_gateway_and_overwrites_forwarded_ip() -> None:
    root = Path(__file__).resolve().parents[3]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    api_service = compose.split("\n  inference:", maxsplit=1)[0].split(
        "\n  api:", maxsplit=1
    )[1]
    nginx = (root / "infrastructure/nginx/default.conf").read_text(encoding="utf-8")

    assert '\n    expose:\n      - "8000"' in api_service
    assert "\n    ports:" not in api_service
    assert "proxy_set_header X-Forwarded-For $remote_addr;" in nginx
    assert "$proxy_add_x_forwarded_for" not in nginx
