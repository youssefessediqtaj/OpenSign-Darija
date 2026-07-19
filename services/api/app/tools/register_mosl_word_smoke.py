from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, select

from app.db.session import SessionLocal
from app.models.enums import InputModality, ModelStatus, RecognitionTaskType
from app.models.sign import ModelVersion

MODEL_NAME = "mosl-word-smoke-v1"
MODEL_VERSION = "0.1.0-smoke"
REQUIRED_MODEL_VERSION_COLUMNS = {
    "architecture",
    "feature_schema_version",
    "labels_json",
    "thresholds_json",
    "calibration_json",
    "checksum",
    "size_bytes",
    "task_type",
    "input_modality",
    "source_dataset_versions",
    "supported_classes",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def register_model(artifact_dir: Path) -> dict[str, Any]:
    artifact_dir = artifact_dir.resolve()
    validation_path = artifact_dir / "package-validation.json"
    if not validation_path.exists():
        raise RuntimeError(
            "package-validation.json is missing; run make ml-validate-word-smoke-model"
        )
    validation = read_json(validation_path)
    if not validation.get("valid"):
        raise RuntimeError("package-validation.json is not valid; rerun smoke package validation")

    labels = [str(label) for label in validation.get("labels", [])]
    if not labels:
        raise RuntimeError("validated smoke package has no labels")
    label_values: list[object] = list(labels)
    checksums = validation.get("checksums", {})
    model_checksum = checksums.get("model.onnx")
    if not isinstance(model_checksum, str) or len(model_checksum) != 64:
        raise RuntimeError("validated smoke package is missing model.onnx checksum")

    metrics = read_json(artifact_dir / "metrics.json")
    onnx_validation = read_json(artifact_dir / "onnx-validation.json")
    dataset_checksum = (artifact_dir / "dataset-manifest-checksum.txt").read_text(
        encoding="utf-8"
    ).strip()

    with SessionLocal() as db:
        columns = {
            column["name"] for column in inspect(db.get_bind()).get_columns("model_versions")
        }
        missing_columns = sorted(REQUIRED_MODEL_VERSION_COLUMNS - columns)
        if missing_columns:
            raise RuntimeError(
                "model_versions schema is not migrated for MoSL registration; "
                f"missing columns: {', '.join(missing_columns)}"
            )
        model = db.scalar(
            select(ModelVersion).where(
                ModelVersion.name == MODEL_NAME,
                ModelVersion.semantic_version == MODEL_VERSION,
                ModelVersion.task_type == RecognitionTaskType.WORD_ISOLATED,
            )
        )
        created = model is None
        if model is None:
            model = ModelVersion(name=MODEL_NAME, semantic_version=MODEL_VERSION)

        model.status = ModelStatus.VALIDATED_SMOKE
        model.task_type = RecognitionTaskType.WORD_ISOLATED
        model.input_modality = InputModality.LANDMARK_SEQUENCE
        model.architecture = "bidirectional-gru"
        model.feature_schema_version = "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
        model.source_dataset_versions = [
            {
                "source_dataset_version": "source-import-v1",
                "dataset_manifest_checksum": dataset_checksum,
            }
        ]
        model.supported_classes = label_values
        model.vocabulary_size = len(labels)
        model.description = (
            "MoSL WORD_ISOLATED smoke model for development-only end-to-end validation; "
            "not production-ready."
        )
        model.labels_json = label_values
        model.metrics_json = {
            **metrics,
            "production_ready": False,
            "package_validation": {
                "valid": True,
                "report_path": validation_path.as_posix(),
                "warnings": validation.get("warnings", []),
            },
            "onnx_validation": onnx_validation,
        }
        model.thresholds_json = {
            "unknown_threshold": 0.6,
            "margin_threshold": 0.15,
            "source": "inference_defaults_for_smoke_validation",
        }
        model.calibration_json = {"temperature": 1.0, "source": "default_smoke"}
        model.artifact_path = artifact_dir.as_posix()
        model.checksum = model_checksum
        model.size_bytes = (artifact_dir / "model.onnx").stat().st_size
        model.is_active = bool(model.is_active)
        db.add(model)
        db.commit()
        db.refresh(model)
        return {
            "created": created,
            "id": model.id,
            "name": model.name,
            "semantic_version": model.semantic_version,
            "status": model.status.value,
            "task_type": model.task_type.value,
            "is_active": model.is_active,
            "artifact_path": model.artifact_path,
            "checksum": model.checksum,
            "vocabulary_size": model.vocabulary_size,
            "supported_classes": model.supported_classes,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register the validated MoSL smoke model in the API DB."
    )
    parser.add_argument(
        "--artifact-dir", type=Path, default=Path("artifacts/models/mosl-word-smoke-v1")
    )
    args = parser.parse_args()
    print(json.dumps(register_model(args.artifact_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
