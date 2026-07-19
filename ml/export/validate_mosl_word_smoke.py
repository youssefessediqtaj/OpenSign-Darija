from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "model.onnx",
    "labels.json",
    "landmark-schema.json",
    "preprocessing.json",
    "metrics.json",
    "onnx-validation.json",
    "model-card.md",
    "checksums.json",
    "training-config.yaml",
    "dataset-manifest-checksum.txt",
}
CHECKSUM_EXCLUDED_FILES = {"checksums.json", "package-validation.json"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: invalid JSON ({exc})")
        return None


def validate_checksums(
    artifact_dir: Path, expected: dict[str, str], errors: list[str]
) -> dict[str, str]:
    actual = {
        path.name: sha256_file(path)
        for path in sorted(artifact_dir.iterdir())
        if path.is_file() and path.name not in CHECKSUM_EXCLUDED_FILES
    }
    for name, checksum in actual.items():
        if expected.get(name) != checksum:
            errors.append(f"checksums.json mismatch for {name}")
    for name in sorted(set(expected) - set(actual)):
        errors.append(f"checksums.json references missing file {name}")
    return actual


def validate_onnx(
    artifact_dir: Path, label_count: int, errors: list[str]
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        import onnx
        import onnxruntime as ort
    except ModuleNotFoundError as exc:
        errors.append(f"ONNX validation dependencies unavailable: {exc}")
        return report

    onnx_path = artifact_dir / "model.onnx"
    try:
        onnx.checker.check_model(str(onnx_path))
        session = ort.InferenceSession(
            str(onnx_path), providers=["CPUExecutionProvider"]
        )
    except Exception as exc:
        errors.append(f"model.onnx failed ONNX Runtime load/check: {exc}")
        return report

    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if len(inputs) != 1:
        errors.append(f"model.onnx expected 1 input, found {len(inputs)}")
    if len(outputs) != 1:
        errors.append(f"model.onnx expected 1 output, found {len(outputs)}")
    if inputs:
        report["input_name"] = inputs[0].name
        report["input_shape"] = list(inputs[0].shape)
        if inputs[0].name != "landmarks":
            errors.append("model.onnx input must be named landmarks")
        if list(inputs[0].shape)[1:] != [60, 75, 3]:
            errors.append(
                f"model.onnx input shape must end with [60, 75, 3], got {inputs[0].shape}"
            )
    if outputs:
        report["output_name"] = outputs[0].name
        report["output_shape"] = list(outputs[0].shape)
        output_shape = list(outputs[0].shape)
        if outputs[0].name != "logits":
            errors.append("model.onnx output must be named logits")
        if len(output_shape) != 2 or output_shape[1] != label_count:
            errors.append(
                f"model.onnx output shape must be [batch, {label_count}], got {output_shape}"
            )
    return report


def validate_artifact_dir(artifact_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not artifact_dir.exists():
        return {
            "valid": False,
            "errors": [f"artifact directory not found: {artifact_dir}"],
            "warnings": [],
        }
    missing = sorted(
        name for name in REQUIRED_FILES if not (artifact_dir / name).exists()
    )
    errors.extend(f"missing required file {name}" for name in missing)

    labels = (
        read_json(artifact_dir / "labels.json", errors)
        if "labels.json" not in missing
        else None
    )
    schema = (
        read_json(artifact_dir / "landmark-schema.json", errors)
        if "landmark-schema.json" not in missing
        else None
    )
    preprocessing = (
        read_json(artifact_dir / "preprocessing.json", errors)
        if "preprocessing.json" not in missing
        else None
    )
    metrics = (
        read_json(artifact_dir / "metrics.json", errors)
        if "metrics.json" not in missing
        else None
    )
    onnx_validation = (
        read_json(artifact_dir / "onnx-validation.json", errors)
        if "onnx-validation.json" not in missing
        else None
    )
    checksums = (
        read_json(artifact_dir / "checksums.json", errors)
        if "checksums.json" not in missing
        else None
    )

    if (
        not isinstance(labels, list)
        or not labels
        or any(not isinstance(label, str) for label in labels)
    ):
        errors.append("labels.json must be a non-empty string list")
        labels = []
    if schema:
        if schema.get("schema_version") != "OPEN_SIGNE_LANDMARK_SCHEMA_V1":
            errors.append(
                "landmark-schema.json schema_version must be OPEN_SIGNE_LANDMARK_SCHEMA_V1"
            )
        if schema.get("recognition_mode") != "WORD_ISOLATED":
            errors.append("landmark-schema.json recognition_mode must be WORD_ISOLATED")
        if schema.get("landmarks") != 75 or schema.get("coordinates") != 3:
            errors.append(
                "landmark-schema.json must declare 75 landmarks and 3 coordinates"
            )
    if preprocessing:
        if preprocessing.get("normalization") != "shoulder_centered_v1":
            errors.append(
                "preprocessing.json normalization must be shoulder_centered_v1"
            )
        if preprocessing.get("frames") != 60:
            errors.append("preprocessing.json frames must be 60")
    if metrics:
        metric_scope = str(metrics.get("metric_scope", ""))
        if "SMOKE TEST ONLY" not in metric_scope:
            warnings.append("metrics.json does not clearly mark smoke-only metrics")
    if onnx_validation and onnx_validation.get("status") != "passed":
        errors.append("onnx-validation.json status must be passed")
    actual_checksums = (
        validate_checksums(artifact_dir, checksums, errors)
        if isinstance(checksums, dict)
        else {}
    )
    onnx_report = (
        validate_onnx(artifact_dir, len(labels), errors)
        if labels and "model.onnx" not in missing
        else {}
    )

    training_config = artifact_dir / "training-config.yaml"
    if training_config.exists():
        text = training_config.read_text(encoding="utf-8")
        for required_text in [
            "VALIDATED_SMOKE",
            "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
            "SMOKE TEST ONLY",
        ]:
            if required_text not in text:
                errors.append(f"training-config.yaml must include {required_text}")

    return {
        "valid": not errors,
        "artifact_dir": artifact_dir.as_posix(),
        "required_files": sorted(REQUIRED_FILES),
        "missing": missing,
        "errors": errors,
        "warnings": warnings,
        "labels": labels,
        "vocabulary_size": len(labels),
        "checksums": actual_checksums,
        "onnx": onnx_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the MoSL WORD_ISOLATED smoke model package."
    )
    parser.add_argument(
        "--artifact-dir", type=Path, default=Path("artifacts/models/mosl-word-smoke-v1")
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/models/mosl-word-smoke-v1/package-validation.json"),
    )
    args = parser.parse_args()
    report = validate_artifact_dir(args.artifact_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
