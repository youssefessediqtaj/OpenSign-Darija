"""Local-only, explicitly configured COLORS_V1 experimental ONNX adapter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort  # type: ignore[import-untyped]

LABELS = ["black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"]
COLORS_V1_LABELS = frozenset({
    "black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow",
})
FEATURE_VERSION = "COLORS_V1_VIDEO_V1_EXPERIMENTAL"


class IncompatibleModelOutputError(ValueError):
    """The selected model produced an incompatible output."""


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for part in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(part)
    return hasher.hexdigest()


class ExperimentalColorsModel:
    """Validate a private registry and expose uncalibrated logits as diagnostics only."""

    def __init__(
        self, registry_path: str, dataset_manifest_path: str | None = None,
        expected_version: str | None = None,
    ) -> None:
        registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        if expected_version is not None and registry.get("model_version") != expected_version:
            raise ValueError("selected model version does not match registry")
        if dataset_manifest_path is not None:
            manifest = Path(dataset_manifest_path)
            if (
                not manifest.is_file()
                or manifest.is_symlink()
                or digest(manifest) != registry.get("dataset_manifest_hash")
            ):
                raise ValueError("model dataset fingerprint does not match current manifest")
        if (
            registry.get("model_id") != "colors_v1_gru_experimental"
            or registry.get("dataset_id") != "colors_v1"
            or registry.get("feature_schema_version") != FEATURE_VERSION
            or registry.get("labels") != LABELS
            or frozenset(registry.get("labels", [])) != COLORS_V1_LABELS
            or registry.get("label_mapping_version") != "colors_v1_semantic_1"
            or registry.get("training_status") not in {"SMOKE_ONLY", "LEARNING_DIAGNOSTIC"}
            or registry.get("evaluation_status") != "EVALUATION_PENDING"
            or registry.get("model_state") != "EXPERIMENTAL"
            or registry.get("activation_status") != "INACTIVE"
            or registry.get("calibration_status") != "UNCALIBRATED"
        ):
            raise ValueError("incompatible experimental model registry")
        for kind in ("onnx", "checkpoint", "report"):
            original = Path(registry[f"{kind}_path"])
            # Registries are created with absolute host paths; in the local container,
            # resolve only the known COLORS_V1 artifact suffix under the mounted registry.
            path = original
            if not path.exists() and "colors_v1" in original.parts:
                suffix = original.parts[original.parts.index("colors_v1") + 1 :]
                path = Path(registry_path).parent.joinpath(*suffix)
            registry[f"{kind}_path"] = str(path)
            if (
                not path.is_file()
                or path.is_symlink()
                or digest(path) != registry[f"{kind}_sha256"]
            ):
                raise ValueError(f"{kind} artifact is missing or has a checksum mismatch")
        report = json.loads(Path(registry["report_path"]).read_text(encoding="utf-8"))
        training_status = registry["training_status"]
        if (
            report.get("dataset") != "colors_v1"
            or report.get("feature_version") != FEATURE_VERSION
            or report.get("labels") != LABELS
            or report.get("manifest_sha256") != registry.get("dataset_manifest_hash")
            or report.get("calibration") != "UNAVAILABLE"
            or (training_status == "SMOKE_ONLY" and (
                report.get("status") != "SMOKE_ONLY_NOT_VALIDATED"
                or report.get("activation") != "DISABLED"
            ))
            or (training_status == "LEARNING_DIAGNOSTIC" and (
                report.get("status") != "EXPERIMENTAL_INACTIVE"
                or report.get("evaluation") != "NO_INDEPENDENT_EVALUATION"
                or not registry.get("experiment_id")
                or report.get("experiment_id") != registry.get("experiment_id")
            ))
        ):
            raise ValueError("experimental training metadata mismatch")
        session = ort.InferenceSession(registry["onnx_path"], providers=["CPUExecutionProvider"])
        inputs, outputs = session.get_inputs(), session.get_outputs()
        if (
            len(inputs) != 1
            or inputs[0].name != "landmarks"
            or inputs[0].shape[1:] != [60, 75, 3]
            or inputs[0].type != "tensor(float)"
            or len(outputs) != 1
            or outputs[0].name != "logits"
            or outputs[0].shape[1:] != [len(LABELS)]
        ):
            raise ValueError("incompatible experimental ONNX shape")
        self.registry: dict[str, Any] = registry
        self.session = session

    def verify_artifacts(self) -> None:
        """Recheck cached model artifacts before each use."""
        for kind in ("onnx", "checkpoint", "report"):
            path = Path(self.registry[f"{kind}_path"])
            if (
                not path.is_file()
                or path.is_symlink()
                or digest(path) != self.registry[f"{kind}_sha256"]
            ):
                raise ValueError(f"{kind} artifact is missing or has a checksum mismatch")

    def predict(
        self,
        landmarks: np.ndarray,
        mask: np.ndarray,
        usable_frames: int,
        *,
        include_candidate: bool,
        include_trace: bool = False,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "model_id": self.registry["model_id"],
            "model_version": self.registry["model_version"],
            "recognition_state": "UNKNOWN_SIGN",
            "semantic_label": None,
            "sign_variant_id": None,
            "candidate": None,
            "raw_score": None,
            "calibration_status": "UNCALIBRATED",
            "experimental": True,
        }
        if self.registry.get("experiment_id"):
            response["experiment_id"] = self.registry["experiment_id"]
        if (
            landmarks.shape != (60, 75, 3)
            or mask.shape != (60, 75)
            or not np.isfinite(landmarks).all()
        ):
            response["recognition_state"] = "PREPROCESSING_ERROR"
            return response
        if not np.any(mask[:, 33:]):
            response["recognition_state"] = "NO_HAND_DETECTED"
            return response
        if usable_frames < 12:
            response["recognition_state"] = "INSUFFICIENT_FRAMES"
            return response
        logits = self.session.run(None, {"landmarks": landmarks[None].astype(np.float32)})[0]
        if logits.shape != (1, len(LABELS)) or not np.isfinite(logits).all():
            raise IncompatibleModelOutputError("invalid experimental model output")
        if include_trace:
            order = np.argsort(-logits[0], kind="stable")[:3]
            response["diagnostics"] = {
                "feature_schema_version": FEATURE_VERSION,
                "output_shape": list(logits.shape),
                "top_three": [
                    {"label": LABELS[int(i)], "raw_score": float(logits[0, i])} for i in order
                ],
            }
        if include_candidate:
            index = int(np.argmax(logits[0]))
            response["candidate"] = LABELS[index]
            response["raw_score"] = float(logits[0, index])
        return response
