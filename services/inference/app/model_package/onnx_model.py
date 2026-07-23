from __future__ import annotations

import hashlib
import json
import re
from math import isclose, isfinite
from pathlib import Path
from typing import Protocol, cast

import numpy as np

from app.core.config import get_settings
from app.model_package.metadata import ModelMetadata
from app.schemas.prediction import (
    ConfidenceLevel,
    Decision,
    PredictionItem,
    WordLandmarkSequenceRequest,
)

EXPECTED_INPUT_SHAPE: list[str | int] = ["batch", 60, 75, 3]
EXPECTED_LANDMARK_SCHEMA = "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
EXPECTED_RECOGNITION_MODE = "WORD_ISOLATED"
EXPECTED_NORMALIZATION = "shoulder_centered_v1"
RUNTIME_PACKAGE_FILES = (
    "model.onnx",
    "labels.json",
    "supported-signs.json",
    "confidence-calibration.json",
    "landmark-schema.json",
    "preprocessing.json",
    "training-split-provenance.json",
    "dataset-manifest-checksum.txt",
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class RuntimeNode(Protocol):
    name: str
    shape: list[str | int | None]
    type: str


class RuntimeSession(Protocol):
    def get_inputs(self) -> list[RuntimeNode]: ...

    def get_outputs(self) -> list[RuntimeNode]: ...

    def run(
        self,
        output_names: list[str] | None,
        input_feed: dict[str, np.ndarray],
    ) -> list[np.ndarray]: ...


def _read_json(path: Path, display_name: str) -> object:
    try:
        parsed: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{display_name} is not valid JSON") from exc
    return parsed


def _required_file(path: Path, display_name: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{display_name} is required")


def _finite_number(data: dict[str, object], key: str, display_name: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError(f"{display_name} {key} is required")
    return float(value)


def _verify_checksums(checksums_path: Path, package_files: dict[str, Path]) -> None:
    _required_file(checksums_path, "checksums.json")
    manifest_data = _read_json(checksums_path, "checksums.json")
    if not isinstance(manifest_data, dict):
        raise ValueError("checksums.json must contain an object")
    manifest = cast(dict[str, object], manifest_data)
    for filename in RUNTIME_PACKAGE_FILES:
        expected_digest = manifest.get(filename)
        if not isinstance(expected_digest, str) or not SHA256_PATTERN.fullmatch(expected_digest):
            raise ValueError(f"checksums.json has no valid SHA-256 for {filename}")
        actual_digest = hashlib.sha256(package_files[filename].read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            raise ValueError(f"checksum mismatch for {filename}")


class OnnxModel:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.feature_schema_version != EXPECTED_LANDMARK_SCHEMA:
            raise ValueError("FEATURE_SCHEMA_VERSION must be OPEN_SIGNE_LANDMARK_SCHEMA_V1")
        if not settings.model_path:
            raise FileNotFoundError("MODEL_PATH is required")

        model_path = Path(settings.model_path)
        artifact_dir = model_path.parent
        package_files = {
            "model.onnx": model_path,
            "labels.json": Path(settings.labels_path or artifact_dir / "labels.json"),
            "supported-signs.json": Path(
                settings.supported_signs_path or artifact_dir / "supported-signs.json"
            ),
            "confidence-calibration.json": Path(
                settings.calibration_path or artifact_dir / "confidence-calibration.json"
            ),
            "landmark-schema.json": artifact_dir / "landmark-schema.json",
            "preprocessing.json": artifact_dir / "preprocessing.json",
            "training-split-provenance.json": (
                artifact_dir / "training-split-provenance.json"
            ),
            "dataset-manifest-checksum.txt": (
                artifact_dir / "dataset-manifest-checksum.txt"
            ),
        }
        for filename, path in package_files.items():
            _required_file(path, filename)
        if model_path.stat().st_size > settings.model_max_size_bytes:
            raise ValueError("ONNX model exceeds MODEL_MAX_SIZE_BYTES")
        if settings.model_checksum_required:
            _verify_checksums(artifact_dir / "checksums.json", package_files)

        label_keys, label_ar_by_key = self._load_vocabulary(
            package_files["labels.json"],
            package_files["supported-signs.json"],
            settings.model_name,
        )
        calibration = self._load_calibration(package_files["confidence-calibration.json"])
        self._validate_landmark_contract(
            package_files["landmark-schema.json"],
            package_files["preprocessing.json"],
        )
        self._validate_training_provenance(
            package_files["training-split-provenance.json"],
            package_files["dataset-manifest-checksum.txt"],
            label_keys,
            label_ar_by_key,
        )

        import onnxruntime as ort  # type: ignore[import-untyped]

        self.session: RuntimeSession = ort.InferenceSession(
            str(model_path),
            providers=[settings.onnx_execution_provider],
        )
        self._validate_session_contract(len(label_keys))
        self.metadata = ModelMetadata(
            name=settings.model_name,
            version=settings.model_version,
            status="active",
            vocabulary_size=len(label_keys),
            feature_schema_version=settings.feature_schema_version,
            dataset_version=None,
            labels=label_keys,
            label_ar_by_key=label_ar_by_key,
            thresholds={
                "unknown_threshold": calibration["unknown_threshold"],
                "margin_threshold": calibration["margin_threshold"],
            },
            calibration={"temperature": calibration["temperature"]},
        )

    @staticmethod
    def _load_vocabulary(
        labels_path: Path,
        supported_signs_path: Path,
        expected_model_name: str,
    ) -> tuple[list[str], dict[str, str]]:
        labels_data = _read_json(labels_path, "labels.json")
        if not isinstance(labels_data, list) or not labels_data:
            raise ValueError("labels.json must contain a non-empty list")
        if any(not isinstance(label, str) or not label.strip() for label in labels_data):
            raise ValueError("labels.json entries must be non-empty strings")
        label_keys = cast(list[str], labels_data)
        if len(set(label_keys)) != len(label_keys):
            raise ValueError("labels.json must not contain duplicate classes")

        supported_data = _read_json(supported_signs_path, "supported-signs.json")
        if not isinstance(supported_data, dict):
            raise ValueError("supported-signs.json must contain an object")
        supported_signs = cast(dict[str, object], supported_data)
        if supported_signs.get("schema_version") != "OPEN_SIGNE_SUPPORTED_SIGNS_V1":
            raise ValueError("supported-signs.json schema is invalid")
        if supported_signs.get("model_name") != expected_model_name:
            raise ValueError("supported-signs.json model_name does not match runtime model")
        sign_items_data = supported_signs.get("signs")
        if not isinstance(sign_items_data, list):
            raise ValueError("supported-signs.json signs must be a list")

        label_ar_by_key: dict[str, str] = {}
        for sign_data in sign_items_data:
            if not isinstance(sign_data, dict):
                raise ValueError("supported-signs.json sign entries must be objects")
            sign = cast(dict[str, object], sign_data)
            if sign.get("status") != "SUPPORTED_FOR_TRAINING":
                continue
            label_key = sign.get("label_key")
            label_ar = sign.get("label_ar")
            if not isinstance(label_key, str) or not label_key.strip():
                raise ValueError("supported-signs.json label_key is invalid")
            if not isinstance(label_ar, str) or not label_ar.strip():
                raise ValueError("supported-signs.json label_ar is invalid")
            if label_key in label_ar_by_key:
                raise ValueError("supported-signs.json has duplicate label_key values")
            label_ar_by_key[label_key] = label_ar

        if set(label_keys) != set(label_ar_by_key):
            raise ValueError("labels.json and supported-signs.json classes do not match")
        vocabulary_size = supported_signs.get("vocabulary_size")
        if type(vocabulary_size) is not int or vocabulary_size != len(label_keys):
            raise ValueError("supported-signs.json vocabulary_size does not match labels.json")
        return label_keys, label_ar_by_key

    @staticmethod
    def _validate_training_provenance(
        provenance_path: Path,
        manifest_checksum_path: Path,
        label_keys: list[str],
        label_ar_by_key: dict[str, str],
    ) -> None:
        provenance_data = _read_json(
            provenance_path, "training-split-provenance.json"
        )
        if not isinstance(provenance_data, dict):
            raise ValueError("training-split-provenance.json must contain an object")
        provenance = cast(dict[str, object], provenance_data)
        if provenance.get("schema_version") != "OPEN_SIGNE_MOSL_SPLIT_V1":
            raise ValueError("training-split-provenance.json schema is invalid")
        if provenance.get("valid") is not True:
            raise ValueError("training-split-provenance.json must be valid")
        if provenance.get("supported_labels") != label_keys:
            raise ValueError(
                "training-split-provenance.json labels do not match runtime labels"
            )
        expected_index = {label: index for index, label in enumerate(label_keys)}
        if provenance.get("label_index") != expected_index:
            raise ValueError(
                "training-split-provenance.json label index does not match runtime labels"
            )

        checksum = manifest_checksum_path.read_text(encoding="utf-8").strip()
        if not SHA256_PATTERN.fullmatch(checksum):
            raise ValueError("dataset-manifest-checksum.txt is not a valid SHA-256")
        if provenance.get("dataset_manifest_checksum_sha256") != checksum:
            raise ValueError("training provenance manifest checksum does not match package")

        ambiguous_data = provenance.get("ambiguous_label_keys_excluded")
        if not isinstance(ambiguous_data, list) or any(
            not isinstance(label, str) for label in ambiguous_data
        ):
            raise ValueError(
                "training-split-provenance.json ambiguous labels are invalid"
            )
        ambiguous_labels = set(cast(list[str], ambiguous_data))
        if set(label_keys) & ambiguous_labels:
            raise ValueError("runtime labels intersect ambiguous training labels")

        assignments_data = provenance.get("assignments")
        if not isinstance(assignments_data, list) or not assignments_data:
            raise ValueError("training-split-provenance.json assignments are required")
        assigned_labels: set[str] = set()
        displays_by_label: dict[str, set[str]] = {}
        for assignment_data in assignments_data:
            if not isinstance(assignment_data, dict):
                raise ValueError("training provenance assignment is invalid")
            assignment = cast(dict[str, object], assignment_data)
            label = assignment.get("label_key")
            display = assignment.get("label_ar")
            if not isinstance(label, str) or label not in label_ar_by_key:
                raise ValueError("training provenance contains an unpackaged label")
            if not isinstance(display, str) or display != label_ar_by_key[label]:
                raise ValueError("training provenance Arabic mapping does not match package")
            if label in ambiguous_labels:
                raise ValueError("training provenance assignment uses an ambiguous label")
            assigned_labels.add(label)
            displays_by_label.setdefault(label, set()).add(display)
        if assigned_labels != set(label_keys):
            raise ValueError("training provenance does not cover runtime labels exactly")
        if any(len(displays) != 1 for displays in displays_by_label.values()):
            raise ValueError("training provenance label has multiple Arabic mappings")

        for pool_name in ("unknown_calibration", "unknown_test"):
            pool_data = provenance.get(pool_name)
            if not isinstance(pool_data, list):
                raise ValueError(f"training provenance {pool_name} is invalid")
            for sample_data in pool_data:
                if not isinstance(sample_data, dict):
                    raise ValueError(f"training provenance {pool_name} sample is invalid")
                sample = cast(dict[str, object], sample_data)
                label = sample.get("label_key")
                if not isinstance(label, str):
                    raise ValueError(f"training provenance {pool_name} label is invalid")
                if label in label_ar_by_key or label in ambiguous_labels:
                    raise ValueError(
                        f"training provenance {pool_name} contains a forbidden label"
                    )

    @staticmethod
    def _load_calibration(calibration_path: Path) -> dict[str, float]:
        calibration_data = _read_json(calibration_path, "confidence-calibration.json")
        if not isinstance(calibration_data, dict):
            raise ValueError("confidence-calibration.json must contain an object")
        calibration = cast(dict[str, object], calibration_data)
        if calibration.get("schema_version") != "OPEN_SIGNE_CONFIDENCE_CALIBRATION_V1":
            raise ValueError("confidence-calibration.json schema is invalid")
        values = {
            "temperature": _finite_number(
                calibration, "temperature", "confidence-calibration.json"
            ),
            "unknown_threshold": _finite_number(
                calibration, "unknown_threshold", "confidence-calibration.json"
            ),
            "margin_threshold": _finite_number(
                calibration, "margin_threshold", "confidence-calibration.json"
            ),
        }
        if values["temperature"] <= 0:
            raise ValueError("confidence-calibration.json temperature must be positive")
        for key in ("unknown_threshold", "margin_threshold"):
            if not 0 <= values[key] <= 1:
                raise ValueError(f"confidence-calibration.json {key} must be in [0, 1]")

        selected_data = calibration.get("selected_operating_point")
        if selected_data is not None:
            if not isinstance(selected_data, dict):
                raise ValueError("confidence-calibration.json selected_operating_point is invalid")
            selected = cast(dict[str, object], selected_data)
            for key in ("unknown_threshold", "margin_threshold"):
                selected_value = _finite_number(
                    selected,
                    key,
                    "confidence-calibration.json selected_operating_point",
                )
                if not isclose(selected_value, values[key], rel_tol=0, abs_tol=1e-12):
                    raise ValueError(
                        f"confidence-calibration.json {key} disagrees with selected_operating_point"
                    )
        return values

    @staticmethod
    def _validate_landmark_contract(schema_path: Path, preprocessing_path: Path) -> None:
        schema_data = _read_json(schema_path, "landmark-schema.json")
        if not isinstance(schema_data, dict):
            raise ValueError("landmark-schema.json must contain an object")
        schema = cast(dict[str, object], schema_data)
        expected_schema_values: dict[str, object] = {
            "schema_version": EXPECTED_LANDMARK_SCHEMA,
            "recognition_mode": EXPECTED_RECOGNITION_MODE,
            "input_name": "landmarks",
            "input_shape": EXPECTED_INPUT_SHAPE,
            "pose_landmarks": 33,
            "left_hand_landmarks": 21,
            "right_hand_landmarks": 21,
            "coordinates": ["x", "y", "z"],
            "dtype": "float32",
        }
        for key, expected in expected_schema_values.items():
            if schema.get(key) != expected:
                raise ValueError(f"landmark-schema.json {key} is incompatible")

        preprocessing_data = _read_json(preprocessing_path, "preprocessing.json")
        if not isinstance(preprocessing_data, dict):
            raise ValueError("preprocessing.json must contain an object")
        preprocessing = cast(dict[str, object], preprocessing_data)
        expected_preprocessing: dict[str, object] = {
            "normalization": EXPECTED_NORMALIZATION,
            "frames": 60,
            "landmarks": 75,
            "coordinates": 3,
        }
        for key, expected in expected_preprocessing.items():
            if preprocessing.get(key) != expected:
                raise ValueError(f"preprocessing.json {key} is incompatible")

    def _validate_session_contract(self, label_count: int) -> None:
        inputs = self.session.get_inputs()
        if len(inputs) != 1:
            raise ValueError("ONNX model must expose exactly one input")
        model_input = inputs[0]
        if model_input.name != "landmarks":
            raise ValueError("ONNX input name must be landmarks")
        if list(model_input.shape) != EXPECTED_INPUT_SHAPE:
            raise ValueError("ONNX input shape must be [batch, 60, 75, 3]")
        if model_input.type != "tensor(float)":
            raise ValueError("ONNX input dtype must be tensor(float)")

        outputs = self.session.get_outputs()
        if len(outputs) != 1:
            raise ValueError("ONNX model must expose exactly one output")
        model_output = outputs[0]
        if model_output.name != "logits":
            raise ValueError("ONNX output name must be logits")
        if list(model_output.shape) != ["batch", label_count]:
            raise ValueError("ONNX output shape must be [batch, label_count]")
        if model_output.type != "tensor(float)":
            raise ValueError("ONNX output dtype must be tensor(float)")

    def warmup(self) -> None:
        """Exercise the exact tensor contract before readiness is reported."""

        outputs = self.session.run(
            None,
            {"landmarks": np.zeros((1, 60, 75, 3), dtype=np.float32)},
        )
        expected_shape = (1, self.metadata.vocabulary_size)
        if len(outputs) != 1 or np.asarray(outputs[0]).shape != expected_shape:
            raise RuntimeError(f"ONNX warmup output must have shape {expected_shape}")
        if not np.isfinite(np.asarray(outputs[0])).all():
            raise RuntimeError("ONNX warmup output contains NaN or infinity")

    def predict(
        self,
        payload: WordLandmarkSequenceRequest,
    ) -> tuple[list[PredictionItem], Decision, ConfidenceLevel, float]:
        landmarks = np.asarray(
            [frame.landmarks for frame in payload.frames],
            dtype=np.float32,
        )[None, :, :, :]
        if landmarks.shape != (1, 60, 75, 3):
            raise ValueError("landmarks must have shape [1, 60, 75, 3]")
        if not np.isfinite(landmarks).all():
            raise ValueError("landmarks contain NaN or infinity")

        outputs = self.session.run(None, {"landmarks": landmarks})
        if len(outputs) != 1:
            raise RuntimeError("ONNX runtime returned an unexpected output count")
        raw_logits = np.asarray(outputs[0])
        expected_shape = (1, self.metadata.vocabulary_size)
        if raw_logits.shape != expected_shape:
            raise RuntimeError(f"ONNX runtime logits must have shape {expected_shape}")
        if not np.isfinite(raw_logits).all():
            raise RuntimeError("ONNX runtime logits contain NaN or infinity")

        logits = raw_logits[0].astype(np.float64, copy=False)
        scaled = logits / self.metadata.calibration["temperature"]
        scaled -= scaled.max()
        exp = np.exp(scaled)
        denominator = float(exp.sum())
        if not isfinite(denominator) or denominator <= 0:
            raise RuntimeError("ONNX runtime logits cannot be normalized")
        probabilities = exp / denominator
        order = np.argsort(probabilities)[::-1][:3]
        predictions = [
            PredictionItem(
                label=self.metadata.labels[int(index)],
                label_ar=self.metadata.label_ar_by_key[self.metadata.labels[int(index)]],
                confidence=float(probabilities[int(index)]),
                rank=rank,
            )
            for rank, index in enumerate(order, start=1)
        ]
        top = float(probabilities[int(order[0])])
        margin = (
            float(probabilities[int(order[0])] - probabilities[int(order[1])])
            if len(order) > 1
            else top
        )
        if top < self.metadata.thresholds["unknown_threshold"]:
            return predictions, "unknown", "low", 1.0 - top
        if margin < self.metadata.thresholds["margin_threshold"]:
            return predictions, "uncertain", "medium", 1.0 - top
        return predictions, "known", "high", 1.0 - top
