import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app, create_app

TOKEN = "local_test_token_2026_only"
PAYLOAD = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "tests/fixtures/recognition/word-recognition-v1-valid.json"
    ).read_text()
)
PATH = "/api/v1/recognitions/colors-experimental"


def test_disabled_by_default() -> None:
    assert PATH not in app.openapi()["paths"]


def test_local_gate_and_candidate_are_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()
    try:
        dev = create_app()
        local = TestClient(dev, client=("127.0.0.1", 5000))
        remote = TestClient(dev, client=("192.0.2.2", 5000))
        assert local.post(PATH, json=PAYLOAD).status_code == 403
        headers = {"x-colors-dev-token": TOKEN}
        assert remote.post(PATH, json=PAYLOAD, headers=headers).status_code == 403
        assert (
            local.post(
                PATH, json=PAYLOAD, headers={**headers, "x-forwarded-for": "127.0.0.1"}
            ).status_code
            == 403
        )
        malformed = {**PAYLOAD, "frames": []}
        assert local.post(PATH, json=malformed, headers=headers).status_code == 422

        class Response:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict[str, Any]:
                return {
                    "model_id": "colors_v1_gru_experimental",
                    "model_version": "0.1.0-smoke",
                    "recognition_state": "UNKNOWN_SIGN",
                    "semantic_label": None,
                    "sign_variant_id": None,
                    "candidate": "blue",
                    "raw_score": 0.1,
                    "calibration_status": "UNCALIBRATED",
                    "experimental": True,
                }

        class AsyncClient:
            def __init__(self, **kwargs: Any) -> None:
                pass

            async def __aenter__(self) -> "AsyncClient":
                return self

            async def __aexit__(self, *args: Any) -> None:
                pass

            async def post(self, *args: Any, **kwargs: Any) -> Response:
                assert kwargs["headers"]["x-colors-dev-token"] == TOKEN
                assert kwargs["params"]["diagnostic"] == "true"
                return Response()

        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", AsyncClient)
        response = local.post(PATH + "?diagnostic=true", json=PAYLOAD, headers=headers)
        assert response.status_code == 200
        assert response.json()["recognition_state"] == "UNKNOWN_SIGN"
        assert response.json()["candidate"] == "blue"
        assert response.json()["semantic_label"] is None
    finally:
        get_settings.cache_clear()


def test_unavailable_inference_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()
    try:
        dev = create_app()
        local = TestClient(dev, client=("127.0.0.1", 5000))

        class Unavailable:
            def __init__(self, **kwargs: Any) -> None:
                pass

            async def __aenter__(self) -> "Unavailable":
                return self

            async def __aexit__(self, *args: Any) -> None:
                pass

            async def post(self, *args: Any, **kwargs: Any) -> Any:
                raise httpx.ConnectError("offline")

        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", Unavailable)
        assert (
            local.post(PATH, json=PAYLOAD, headers={"x-colors-dev-token": TOKEN}).status_code == 503
        )
    finally:
        get_settings.cache_clear()
