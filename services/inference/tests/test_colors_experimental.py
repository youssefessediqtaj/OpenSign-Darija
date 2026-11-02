import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app, create_app
from app.runtime.colors_model import (
    FEATURE_VERSION,
    LABELS,
    ExperimentalColorsModel,
    IncompatibleModelOutputError,
)

TOKEN = "local_test_token_2026_only"
PAYLOAD = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "tests/fixtures/recognition/word-recognition-v1-valid.json"
    ).read_text()
)
PATH = "/predict/colors-experimental"


def test_disabled_by_default() -> None:
    assert PATH not in app.openapi()["paths"]


def test_registry_integrity_shapes_and_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("current dataset", encoding="utf-8")
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    registry: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental",
        "model_version": "test",
        "dataset_id": "colors_v1",
        "feature_schema_version": FEATURE_VERSION,
        "labels": LABELS,
        "model_state": "EXPERIMENTAL",
        "activation_status": "INACTIVE",
        "calibration_status": "UNCALIBRATED",
        "label_mapping_version": "colors_v1_semantic_1",
        "training_status": "SMOKE_ONLY",
        "evaluation_status": "EVALUATION_PENDING",
        "dataset_manifest_hash": manifest_hash,
    }
    for kind in ("onnx", "checkpoint", "report"):
        path = tmp_path / kind
        content = (
            kind.encode()
            if kind != "report"
            else json.dumps(
                {
                    "dataset": "colors_v1",
                    "feature_version": FEATURE_VERSION,
                    "labels": LABELS,
                    "manifest_sha256": manifest_hash,
                    "status": "SMOKE_ONLY_NOT_VALIDATED",
                    "activation": "DISABLED",
                    "calibration": "UNAVAILABLE",
                }
            ).encode()
        )
        path.write_bytes(content)
        registry[f"{kind}_path"] = str(path)
        registry[f"{kind}_sha256"] = hashlib.sha256(content).hexdigest()
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry))

    class Session:
        def get_inputs(self) -> list[Any]:
            return [
                SimpleNamespace(name="landmarks", shape=["batch", 60, 75, 3], type="tensor(float)")
            ]

        def get_outputs(self) -> list[Any]:
            return [SimpleNamespace(name="logits", shape=["batch", 9])]

        def run(self, *args: Any, **kwargs: Any) -> list[Any]:
            return [np.array([[0, 1, 0, 0, 0, 0, 0, 0, 0]], dtype=np.float32)]

    monkeypatch.setattr(
        "app.runtime.colors_model.ort.InferenceSession", lambda *args, **kwargs: Session()
    )
    model = ExperimentalColorsModel(str(path), str(manifest))
    with pytest.raises(ValueError, match="selected model version"):
        ExperimentalColorsModel(str(path), str(manifest), "other-version")
    selected = ExperimentalColorsModel(str(path), str(manifest), "test")
    assert selected.registry["model_version"] == "test"
    from app.api.colors_experimental import _load_model, local_model

    monkeypatch.setenv("COLORS_EXPERIMENTAL_REGISTRY", str(path))
    monkeypatch.setenv("COLORS_EXPERIMENTAL_DATASET_MANIFEST", str(manifest))
    monkeypatch.setenv("COLORS_EXPERIMENTAL_MODEL_VERSION", "test")
    get_settings.cache_clear()
    _load_model.cache_clear()
    local_model()
    # A cached session must not survive replacement or corruption of its artifact.
    (tmp_path / "onnx").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        local_model()
    (tmp_path / "onnx").write_bytes(b"onnx")
    manifest.write_text("changed dataset", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        ExperimentalColorsModel(str(path), str(manifest))
    with pytest.raises(ValueError, match="fingerprint"):
        local_model()
    manifest.write_text("current dataset", encoding="utf-8")
    _load_model.cache_clear()
    get_settings.cache_clear()
    x = np.ones((60, 75, 3), dtype=np.float32)
    mask = np.ones((60, 75), dtype=np.float32)
    assert model.predict(x, mask, 60, include_candidate=False)["candidate"] is None
    result = model.predict(x, mask, 60, include_candidate=True, include_trace=True)
    assert result["candidate"] == "blue" and result["recognition_state"] == "UNKNOWN_SIGN"
    assert result["semantic_label"] is None and result["calibration_status"] == "UNCALIBRATED"
    assert result["diagnostics"]["output_shape"] == [1, 9]
    assert result["diagnostics"]["top_three"][0] == {"label": "blue", "raw_score": 1.0}
    assert len(result["diagnostics"]["top_three"]) == 3
    model.session = SimpleNamespace(run=lambda *args, **kwargs: [np.zeros((1, 3))])
    with pytest.raises(IncompatibleModelOutputError):
        model.predict(x, mask, 60, include_candidate=True)
    model.session = Session()
    assert "diagnostics" not in model.predict(x, mask, 60, include_candidate=True)
    assert (
        model.predict(x, mask, 2, include_candidate=True)["recognition_state"]
        == "INSUFFICIENT_FRAMES"
    )
    mask[:, 33:] = 0
    assert (
        model.predict(x, mask, 60, include_candidate=True)["recognition_state"]
        == "NO_HAND_DETECTED"
    )
    assert (
        model.predict(x[:2], mask, 60, include_candidate=True)["recognition_state"]
        == "PREPROCESSING_ERROR"
    )

    class WrongShape(Session):
        def get_outputs(self) -> list[Any]:
            return [SimpleNamespace(name="logits", shape=["batch", 8])]

    monkeypatch.setattr(
        "app.runtime.colors_model.ort.InferenceSession", lambda *args, **kwargs: WrongShape()
    )
    with pytest.raises(ValueError, match="shape"):
        ExperimentalColorsModel(str(path))
    monkeypatch.setattr(
        "app.runtime.colors_model.ort.InferenceSession", lambda *args, **kwargs: Session()
    )
    (tmp_path / "onnx").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        ExperimentalColorsModel(str(path))


@pytest.mark.parametrize(
    "failure", ["registry", "model", "fingerprint", "schema", "corrupt", "initialize"]
)
def test_load_failures_return_not_ready_without_legacy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    from app.api.colors_experimental import _load_model

    manifest = tmp_path / "manifest"
    manifest.write_text("dataset")
    fingerprint = hashlib.sha256(manifest.read_bytes()).hexdigest()
    registry: dict[str, Any] = {
        "model_id": "colors_v1_gru_experimental", "model_version": "test",
        "dataset_id": "colors_v1", "feature_schema_version": FEATURE_VERSION,
        "labels": LABELS, "label_mapping_version": "colors_v1_semantic_1",
        "training_status": "SMOKE_ONLY", "evaluation_status": "EVALUATION_PENDING",
        "model_state": "EXPERIMENTAL", "activation_status": "INACTIVE",
        "calibration_status": "UNCALIBRATED", "dataset_manifest_hash": fingerprint,
    }
    report = {"dataset": "colors_v1", "feature_version": FEATURE_VERSION, "labels": LABELS,
              "manifest_sha256": fingerprint, "status": "SMOKE_ONLY_NOT_VALIDATED",
              "activation": "DISABLED", "calibration": "UNAVAILABLE"}
    for kind in ("onnx", "checkpoint", "report"):
        artifact = tmp_path / kind
        artifact.write_text(json.dumps(report) if kind == "report" else kind)
        registry[f"{kind}_path"] = str(artifact)
        registry[f"{kind}_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if failure == "model":
        (tmp_path / "onnx").unlink()
    elif failure == "corrupt":
        (tmp_path / "onnx").write_text("corrupted")
    elif failure == "fingerprint":
        manifest.write_text("different dataset")
    elif failure == "schema":
        registry["feature_schema_version"] = "legacy"
    registry_path = tmp_path / "registry.json"
    if failure != "registry":
        registry_path.write_text(json.dumps(registry))
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    monkeypatch.setenv("COLORS_EXPERIMENTAL_REGISTRY", str(registry_path))
    monkeypatch.setenv("COLORS_EXPERIMENTAL_DATASET_MANIFEST", str(manifest))
    monkeypatch.setenv("COLORS_EXPERIMENTAL_MODEL_VERSION", "test")
    monkeypatch.setattr("app.runtime.prediction.PredictionService.predict_word",
                        lambda *args: pytest.fail("legacy inference called"))
    get_settings.cache_clear()
    _load_model.cache_clear()
    try:
        client = TestClient(create_app(), client=("127.0.0.1", 5000))
        response = client.post(PATH, json=PAYLOAD, headers={"x-colors-dev-token": TOKEN})
        assert response.json()["recognition_state"] == "MODEL_NOT_READY"
        assert response.json()["candidate"] is None
    finally:
        _load_model.cache_clear()
        get_settings.cache_clear()


def test_enabled_route_requires_loopback_token_and_reports_missing_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_TOKEN", TOKEN)
    get_settings.cache_clear()
    try:
        dev = create_app()
        local = TestClient(dev, client=("127.0.0.1", 5000))
        remote = TestClient(dev, client=("192.0.2.2", 5000))
        headers = {"x-colors-dev-token": TOKEN}
        assert local.post(PATH, json=PAYLOAD).status_code == 403
        assert remote.post(PATH, json=PAYLOAD, headers=headers).status_code == 403
        assert (
            local.post(
                PATH, json=PAYLOAD, headers={**headers, "x-forwarded-for": "127.0.0.1"}
            ).status_code
            == 403
        )
        assert local.post(PATH, json={**PAYLOAD, "frames": []}, headers=headers).status_code == 422
        monkeypatch.setattr(
            "app.api.colors_experimental.local_model",
            lambda: (_ for _ in ()).throw(FileNotFoundError()),
        )
        response = local.post(PATH, json=PAYLOAD, headers=headers)
        assert response.status_code == 200
        assert response.json()["recognition_state"] == "MODEL_NOT_READY"
        traced = local.post(PATH + "?diagnostic=true&trace=true", json=PAYLOAD, headers=headers)
        assert traced.json()["diagnostics"]["failure_stage"] == "model_load"
    finally:
        get_settings.cache_clear()


def test_color_mode_never_loads_legacy_model(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.runtime.model_loader import ModelLoader

    monkeypatch.setenv("COLORS_EXPERIMENTAL_ENABLED", "true")
    get_settings.cache_clear()
    try:
        monkeypatch.setattr(
            "app.runtime.model_loader.OnnxModel",
            lambda: (_ for _ in ()).throw(AssertionError("legacy model loaded")),
        )
        loader = ModelLoader()
        assert loader.state == "EXPERIMENTAL"
        assert loader.model is None
        client = TestClient(create_app(), client=("127.0.0.1", 5000))
        assert client.post("/predict/word", json=PAYLOAD).status_code == 404
    finally:
        get_settings.cache_clear()


def test_service_requires_a_current_manifest_before_loading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.colors_experimental import _load_model, local_model

    monkeypatch.setenv("COLORS_EXPERIMENTAL_DATASET_MANIFEST", "")
    get_settings.cache_clear()
    _load_model.cache_clear()
    try:
        with pytest.raises(ValueError, match="manifest is required"):
            local_model()
    finally:
        _load_model.cache_clear()
        get_settings.cache_clear()


def test_service_requires_explicit_model_version(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.colors_experimental import _load_model, local_model

    monkeypatch.setenv("COLORS_EXPERIMENTAL_DATASET_MANIFEST", "manifest.json")
    monkeypatch.setenv("COLORS_EXPERIMENTAL_MODEL_VERSION", "")
    get_settings.cache_clear()
    _load_model.cache_clear()
    try:
        with pytest.raises(ValueError, match="model version"):
            local_model()
    finally:
        _load_model.cache_clear()
        get_settings.cache_clear()
