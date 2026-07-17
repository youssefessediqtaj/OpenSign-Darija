from __future__ import annotations

import hashlib
import json
from pathlib import Path


REQUIRED_MODEL_FILES = {
    "model.onnx",
    "labels.json",
    "feature_schema.json",
    "thresholds.json",
    "calibration.json",
    "metrics.json",
    "model_card.md",
}


def artifact_checksums(artifact_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for path in sorted(artifact_dir.iterdir()):
        if path.is_file():
            checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return checksums


def validate_artifact_dir(artifact_dir: Path) -> dict[str, object]:
    missing = sorted(file_name for file_name in REQUIRED_MODEL_FILES if not (artifact_dir / file_name).exists())
    checksums = artifact_checksums(artifact_dir) if artifact_dir.exists() else {}
    return {"valid": not missing, "missing": missing, "checksums": checksums}


def write_checksums(artifact_dir: Path) -> None:
    (artifact_dir / "checksums.json").write_text(
        json.dumps(artifact_checksums(artifact_dir), indent=2) + "\n",
        encoding="utf-8",
    )
