import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest

from app.core.config import get_settings
from app.models.onnx_model import OnnxModel
from app.schemas.prediction import WordLandmarkSequenceRequest

RUNTIME_FILES = (
    "model.onnx",
    "labels.json",
    "supported-signs.json",
    "confidence-calibration.json",
    "landmark-schema.json",
    "preprocessing.json",
    "training-split-provenance.json",
    "dataset-manifest-checksum.txt",
)


class FakeInput:
    name = "landmarks"
    shape: list[str | int] = ["batch", 60, 75, 3]
    type = "tensor(float)"


class FakeOutput:
    name = "logits"
    shape: list[str | int] = ["batch", 2]
    type = "tensor(float)"


class FakeInferenceSession:
    logits = np.asarray([[3.0, 0.0]], dtype=np.float32)

    def __init__(self, model_path: str, providers: list[str]) -> None:
        self.model_path = model_path
        self.providers = providers

    def get_inputs(self) -> list[FakeInput]:
        return [FakeInput()]

    def get_outputs(self) -> list[FakeOutput]:
        return [FakeOutput()]

    def run(
        self,
        outputs: list[str] | None,
        inputs: dict[str, np.ndarray],
    ) -> list[np.ndarray]:
        assert outputs is None
        assert inputs["landmarks"].shape == (1, 60, 75, 3)
        return [self.logits]


@pytest.fixture(autouse=True)
def reset_test_state() -> Iterator[None]:
    get_settings.cache_clear()
    FakeInput.shape = ["batch", 60, 75, 3]
    FakeOutput.shape = ["batch", 2]
    FakeInferenceSession.logits = np.asarray([[3.0, 0.0]], dtype=np.float32)
    yield
    get_settings.cache_clear()


def write_checksums(package_dir: Path) -> None:
    manifest = {
        filename: hashlib.sha256((package_dir / filename).read_bytes()).hexdigest()
        for filename in RUNTIME_FILES
    }
    (package_dir / "checksums.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_model_package(
    package_dir: Path,
    *,
    unknown_threshold: float = 0.7,
    margin_threshold: float = 0.2,
    temperature: float = 1.0,
) -> Path:
    package_dir.mkdir()
    model_path = package_dir / "model.onnx"
    model_path.write_bytes(b"fake-onnx")
    (package_dir / "labels.json").write_text(json.dumps(["help", "water"]), encoding="utf-8")
    (package_dir / "supported-signs.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_SUPPORTED_SIGNS_V1",
                "model_name": "mosl-isolated-sign-v1",
                "vocabulary_size": 2,
                "signs": [
                    {
                        "label_key": "help",
                        "label_ar": "عاونّي",
                        "status": "SUPPORTED_FOR_TRAINING",
                    },
                    {
                        "label_key": "water",
                        "label_ar": "ما",
                        "status": "SUPPORTED_FOR_TRAINING",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "confidence-calibration.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_CONFIDENCE_CALIBRATION_V1",
                "method": "temperature_scaling_max_probability_and_margin",
                "temperature": temperature,
                "unknown_threshold": unknown_threshold,
                "margin_threshold": margin_threshold,
                "selected_operating_point": {
                    "unknown_threshold": unknown_threshold,
                    "margin_threshold": margin_threshold,
                },
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "landmark-schema.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                "recognition_mode": "WORD_ISOLATED",
                "input_name": "landmarks",
                "input_shape": ["batch", 60, 75, 3],
                "pose_landmarks": 33,
                "left_hand_landmarks": 21,
                "right_hand_landmarks": 21,
                "coordinates": ["x", "y", "z"],
                "dtype": "float32",
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "preprocessing.json").write_text(
        json.dumps(
            {
                "normalization": "shoulder_centered_v1",
                "frames": 60,
                "landmarks": 75,
                "coordinates": 3,
            }
        ),
        encoding="utf-8",
    )
    manifest_checksum = "a" * 64
    (package_dir / "dataset-manifest-checksum.txt").write_text(
        manifest_checksum + "\n", encoding="utf-8"
    )
    (package_dir / "training-split-provenance.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_MOSL_SPLIT_V1",
                "valid": True,
                "dataset_manifest_checksum_sha256": manifest_checksum,
                "supported_labels": ["help", "water"],
                "label_index": {"help": 0, "water": 1},
                "ambiguous_label_keys_excluded": ["collision"],
                "assignments": [
                    {"label_key": "help", "label_ar": "عاونّي", "split": "train"},
                    {"label_key": "water", "label_ar": "ما", "split": "train"},
                ],
                "unknown_calibration": [],
                "unknown_test": [],
            }
        ),
        encoding="utf-8",
    )
    write_checksums(package_dir)
    return model_path


def configure_real_package(monkeypatch: pytest.MonkeyPatch, model_path: Path) -> None:
    monkeypatch.setenv("MODEL_NAME", "mosl-isolated-sign-v1")
    monkeypatch.setenv("MODEL_VERSION", "1.0.0")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("FEATURE_SCHEMA_VERSION", "OPEN_SIGNE_LANDMARK_SCHEMA_V1")
    monkeypatch.setenv("MODEL_CHECKSUM_REQUIRED", "true")
    monkeypatch.delenv("LABELS_PATH", raising=False)
    monkeypatch.delenv("SUPPORTED_SIGNS_PATH", raising=False)
    monkeypatch.delenv("CALIBRATION_PATH", raising=False)
    get_settings.cache_clear()


def valid_word_payload() -> dict[str, object]:
    return {
        "sequence_id": "123e4567-e89b-12d3-a456-426614174000",
        "captured_at": "2026-07-17T12:00:00Z",
        "recognition_mode": "WORD_ISOLATED",
        "duration_ms": 1600,
        "source_fps": 15,
        "target_frame_count": 60,
        "landmark_count": 75,
        "coordinate_count": 3,
        "coordinate_format": "shoulder_centered_v1",
        "feature_schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
        "frames": [
            {
                "index": index,
                "timestamp_ms": index * 33,
                "landmarks": [[0.1, 0.0, 0.0] for _ in range(75)],
                "presence_mask": [1] * 75,
            }
            for index in range(60)
        ],
        "quality": {
            "detected_hand_ratio": 1,
            "detected_face_ratio": 0,
            "detected_pose_ratio": 1,
            "missing_frame_ratio": 0,
            "movement_score": 0.5,
        },
        "segmentation_kind": "dynamic",
        "segmentation_reliable": True,
        "usable_frame_count": 60,
    }


def test_real_model_loads_complete_package_and_returns_arabic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import onnxruntime as ort

    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    monkeypatch.setattr(ort, "InferenceSession", FakeInferenceSession)

    model = OnnxModel()
    predictions, decision, confidence_level, unknown_probability = model.predict(
        WordLandmarkSequenceRequest(**valid_word_payload())
    )
    assert decision == "known"
    assert confidence_level == "high"
    assert predictions[0].label == "help"
    assert predictions[0].label_ar == "عاونّي"
    assert unknown_probability < 0.1


def test_calibration_controls_unknown_and_margin_decisions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import onnxruntime as ort

    monkeypatch.setattr(ort, "InferenceSession", FakeInferenceSession)
    FakeInferenceSession.logits = np.asarray([[0.1, 0.0]], dtype=np.float32)

    unknown_path = write_model_package(tmp_path / "unknown", unknown_threshold=0.7)
    configure_real_package(monkeypatch, unknown_path)
    unknown_model = OnnxModel()
    _, decision, confidence_level, _ = unknown_model.predict(
        WordLandmarkSequenceRequest(**valid_word_payload())
    )
    assert (decision, confidence_level) == ("unknown", "low")

    uncertain_path = write_model_package(
        tmp_path / "uncertain", unknown_threshold=0.5, margin_threshold=0.2
    )
    configure_real_package(monkeypatch, uncertain_path)
    uncertain_model = OnnxModel()
    _, decision, confidence_level, _ = uncertain_model.predict(
        WordLandmarkSequenceRequest(**valid_word_payload())
    )
    assert (decision, confidence_level) == ("uncertain", "medium")


def test_checksum_verification_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    (model_path.parent / "labels.json").write_text(
        json.dumps(["tampered", "water"]), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="checksum mismatch for labels.json"):
        OnnxModel()


def test_checksum_manifest_is_required_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    (model_path.parent / "checksums.json").unlink()

    with pytest.raises(FileNotFoundError, match="checksums.json is required"):
        OnnxModel()


def test_runtime_rejects_semantically_stale_training_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    provenance_path = model_path.parent / "training-split-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["ambiguous_label_keys_excluded"].append("help")
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    write_checksums(model_path.parent)

    with pytest.raises(ValueError, match="intersect ambiguous"):
        OnnxModel()


def test_runtime_rejects_a_legacy_feature_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    monkeypatch.setenv("FEATURE_SCHEMA_VERSION", "1.0.0")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="FEATURE_SCHEMA_VERSION"):
        OnnxModel()


@pytest.mark.parametrize(
    ("node", "bad_shape", "message"),
    [
        (FakeInput, ["batch", 59, 75, 3], "ONNX input shape"),
        (FakeOutput, ["batch", 3], "ONNX output shape"),
    ],
)
def test_real_model_rejects_malformed_onnx_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    node: type[FakeInput] | type[FakeOutput],
    bad_shape: list[str | int],
    message: str,
) -> None:
    import onnxruntime as ort

    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    monkeypatch.setattr(ort, "InferenceSession", FakeInferenceSession)
    node.shape = bad_shape

    with pytest.raises(ValueError, match=message):
        OnnxModel()


def test_real_model_rejects_incomplete_or_mismatched_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing_path = write_model_package(tmp_path / "missing")
    configure_real_package(monkeypatch, missing_path)
    (missing_path.parent / "supported-signs.json").unlink()
    with pytest.raises(FileNotFoundError, match="supported-signs.json is required"):
        OnnxModel()

    mismatched_path = write_model_package(tmp_path / "mismatched")
    configure_real_package(monkeypatch, mismatched_path)
    (mismatched_path.parent / "supported-signs.json").write_text(
        json.dumps(
            {
                "schema_version": "OPEN_SIGNE_SUPPORTED_SIGNS_V1",
                "model_name": "mosl-isolated-sign-v1",
                "vocabulary_size": 1,
                "signs": [
                    {
                        "label_key": "help",
                        "label_ar": "عاونّي",
                        "status": "SUPPORTED_FOR_TRAINING",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    write_checksums(mismatched_path.parent)
    with pytest.raises(ValueError, match="classes do not match"):
        OnnxModel()


@pytest.mark.parametrize(
    ("field", "value"),
    [("temperature", 0), ("unknown_threshold", 1.1), ("margin_threshold", -0.1)],
)
def test_real_model_rejects_invalid_calibration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: float,
) -> None:
    options = {"temperature": 1.0, "unknown_threshold": 0.7, "margin_threshold": 0.2}
    options[field] = value
    model_path = write_model_package(tmp_path / "package", **options)
    configure_real_package(monkeypatch, model_path)

    with pytest.raises(ValueError, match=field):
        OnnxModel()


@pytest.mark.parametrize(
    ("filename", "field", "value", "message"),
    [
        ("landmark-schema.json", "input_shape", ["batch", 30, 75, 3], "input_shape"),
        ("preprocessing.json", "normalization", "torso_normalized_v1", "normalization"),
    ],
)
def test_real_model_rejects_incompatible_preprocessing_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    field: str,
    value: object,
    message: str,
) -> None:
    model_path = write_model_package(tmp_path / "package")
    configure_real_package(monkeypatch, model_path)
    contract_path = model_path.parent / filename
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract[field] = value
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    write_checksums(model_path.parent)

    with pytest.raises(ValueError, match=message):
        OnnxModel()
