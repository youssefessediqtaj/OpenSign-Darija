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
                    "experiment_id": "test-experiment",
                    "recognition_state": "UNKNOWN_SIGN",
                    "semantic_label": None,
                    "sign_variant_id": None,
                    "candidate": "blue",
                    "raw_score": 0.1,
                    "calibration_status": "UNCALIBRATED",
                    "experimental": True,
                    "diagnostics": {
                        "feature_schema_version": "COLORS_V1_VIDEO_V1_EXPERIMENTAL",
                        "output_shape": [1, 9],
                        "top_three": [
                            {"label": "blue", "raw_score": 0.1},
                            {"label": "pink", "raw_score": 0.0},
                            {"label": "red", "raw_score": -0.1},
                        ],
                        "failure_stage": None,
                    },
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
                assert kwargs["params"]["trace"] == "true"
                return Response()

        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", AsyncClient)
        response = local.post(PATH + "?diagnostic=true&trace=true", json=PAYLOAD, headers=headers)
        assert response.status_code == 200
        assert response.json()["recognition_state"] == "UNKNOWN_SIGN"
        assert response.json()["candidate"] == "blue"
        assert response.json()["experiment_id"] == "test-experiment"
        assert response.json()["semantic_label"] is None
        assert response.json()["diagnostics"]["top_three"][0]["label"] == "blue"
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
            local.post(PATH, json=PAYLOAD, headers={"x-colors-dev-token": TOKEN}).status_code == 502
        )
    finally:
        get_settings.cache_clear()


def test_gateway_returns_model_not_ready_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {"model_id": "colors_v1_gru_experimental", "model_version": "unselected",
                    "recognition_state": "MODEL_NOT_READY", "semantic_label": None,
                    "sign_variant_id": None, "candidate": None, "raw_score": None,
                    "calibration_status": "UNCALIBRATED", "experimental": True}

    class Client:
        def __init__(self, **kwargs: Any) -> None: pass
        async def __aenter__(self) -> "Client": return self
        async def __aexit__(self, *args: Any) -> None: pass
        async def post(self, *args: Any, **kwargs: Any) -> Response: return Response()

    try:
        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", Client)
        client = TestClient(create_app(), client=("127.0.0.1", 5000))
        response = client.post(PATH, json=PAYLOAD, headers={"x-colors-dev-token": TOKEN})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "MODEL_NOT_READY"
        assert response.json()["error"]["details"] == {
            "status": "MODEL_NOT_READY", "prediction": None, "candidate": None,
            "model_id": "colors_v1",
        }
    finally:
        get_settings.cache_clear()


def test_color_mode_rejects_legacy_word_route(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app(), client=("127.0.0.1", 5000))
        assert client.post("/api/v1/recognitions/word", json=PAYLOAD).status_code == 404
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize(
    ("error", "status"),
    [(httpx.ConnectError("offline"), 502), (httpx.ReadTimeout("timeout"), 504)],
)
def test_gateway_distinguishes_inference_network_and_timeout(
    monkeypatch: pytest.MonkeyPatch, error: httpx.HTTPError, status: int
) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()
    try:

        class Unavailable:
            def __init__(self, **kwargs: Any) -> None:
                pass

            async def __aenter__(self) -> "Unavailable":
                return self

            async def __aexit__(self, *args: Any) -> None:
                pass

            async def post(self, *args: Any, **kwargs: Any) -> Any:
                raise error

        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", Unavailable)
        local = TestClient(create_app(), client=("127.0.0.1", 5000))
        assert (
            local.post(PATH, json=PAYLOAD, headers={"x-colors-dev-token": TOKEN}).status_code
            == status
        )
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize(
    "label",
    [
        "black",
        "blue",
        "brown",
        "green",
        "orange",
        "pink",
        "red",
        "white",
        "yellow",
        "père",
        "أب",
        "أحب",
        "سوق",
        "arbitrary",
        "toString",
    ],
)
@pytest.mark.parametrize("field", ["candidate", "diagnostics"])
def test_gateway_enforces_color_allowlist(
    monkeypatch: pytest.MonkeyPatch, label: str, field: str
) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()
    data: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental",
        "model_version": "0.2.0-provisional-v1",
        "recognition_state": "UNKNOWN_SIGN",
        "semantic_label": None,
        "sign_variant_id": None,
        "candidate": "blue",
        "raw_score": 0.1,
        "calibration_status": "UNCALIBRATED",
        "experimental": True,
        "diagnostics": {
            "feature_schema_version": "COLORS_V1_VIDEO_V1_EXPERIMENTAL",
            "output_shape": [1, 9],
            "top_three": [{"label": "blue", "raw_score": 0.1}],
        },
    }
    if field == "candidate":
        data["candidate"] = label
    else:
        data["diagnostics"]["top_three"][0]["label"] = label

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return data

    class Client:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def post(self, url: str, **kwargs: Any) -> Response:
            assert url.endswith("/predict/colors-experimental")
            return Response()

    try:
        monkeypatch.setattr("app.api.v1.colors_experimental.httpx.AsyncClient", Client)
        client = TestClient(create_app(), client=("127.0.0.1", 5000))
        response = client.post(
            PATH + "?diagnostic=true&trace=true",
            json=PAYLOAD,
            headers={"x-colors-dev-token": TOKEN},
        )
        if label in {"black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"}:
            assert response.status_code == 200
        else:
            assert response.status_code == 502
            assert response.json()["error"]["code"] == "INCOMPATIBLE_MODEL_OUTPUT"
            assert label not in response.text
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize(
    "change",
    [
        {"model_id": "legacy-model"},
        {"candidate": "أب"},
        {"candidate": 7},
        {"semantic_label": "blue"},
        {
            "diagnostics": {
                "feature_schema_version": "COLORS_V1_VIDEO_V1_EXPERIMENTAL",
                "output_shape": [1, 3],
                "top_three": [],
            }
        },
        {
            "diagnostics": {
                "feature_schema_version": "COLORS_V1_VIDEO_V1_EXPERIMENTAL",
                "output_shape": [1, 9],
                "top_three": [{"raw_score": 0.1}],
            }
        },
    ],
)
def test_response_schema_rejects_incompatible_data(change: dict[str, Any]) -> None:
    from pydantic import ValidationError

    from app.api.v1.colors_experimental import ExperimentalColorResult

    data: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental",
        "model_version": "0.2.0-provisional-v1",
        "recognition_state": "UNKNOWN_SIGN",
        "semantic_label": None,
        "sign_variant_id": None,
        "candidate": "blue",
        "raw_score": 0.1,
        "calibration_status": "UNCALIBRATED",
        "experimental": True,
    }
    with pytest.raises(ValidationError):
        ExperimentalColorResult.model_validate({**data, **change})


def test_blue_variants_share_semantic_label() -> None:
    config = json.loads(
        (Path(__file__).resolve().parents[3] / "ml/configs/colors_v1.json").read_text()
    )
    blue = next(item for item in config["labels"] if item["id"] == "blue")
    assert set(blue["variants"]) == {"blue_variant_01", "blue_variant_02"}
