"""Create a local immutable registry entry for an experimental color ONNX package."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import onnxruntime as ort

from ml.datasets.colors_v1.validate import sha256

FEATURE_VERSION = "COLORS_V1_VIDEO_V1_EXPERIMENTAL"
LABELS = ["black", "blue", "brown", "green", "orange", "pink", "red", "white", "yellow"]


def register(model_dir: Path, output: Path) -> dict[str, Any]:
    """Check actual artifacts and create an experimental, never-active registry entry."""
    model_dir = model_dir.resolve()
    checkpoint, model, report_path = (model_dir / name for name in ("checkpoint.pt", "model.onnx", "report.json"))
    if not all(path.is_file() and not path.is_symlink() for path in (checkpoint, model, report_path)):
        raise ValueError("checkpoint, ONNX and report must be regular files")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (report.get("dataset") != "colors_v1" or report.get("status") != "SMOKE_ONLY_NOT_VALIDATED"
            or report.get("feature_version") != FEATURE_VERSION or report.get("labels") != LABELS
            or report.get("activation") != "DISABLED" or report.get("calibration") != "UNAVAILABLE"):
        raise ValueError("experimental model metadata is incompatible")
    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    inputs, outputs = session.get_inputs(), session.get_outputs()
    if (len(inputs) != 1 or inputs[0].name != "landmarks" or inputs[0].shape[1:] != [60, 75, 3]
            or inputs[0].type != "tensor(float)" or len(outputs) != 1
            or outputs[0].name != "logits" or outputs[0].shape[1:] != [len(LABELS)]):
        raise ValueError("ONNX model input/output contract is incompatible")
    result = {"model_id": "colors_v1_gru_experimental", "model_version": "0.1.0-smoke",
              "model_type": "bidirectional_gru", "dataset_id": "colors_v1",
              "dataset_manifest_hash": report["manifest_sha256"], "feature_schema_version": FEATURE_VERSION,
              "label_mapping_version": "colors_v1_semantic_1", "labels": LABELS,
              "checkpoint_path": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
              "onnx_path": str(model), "onnx_sha256": sha256(model), "report_path": str(report_path),
              "report_sha256": sha256(report_path),
              "training_configuration": {"epochs": report["epochs"], "seed": report["seed"],
                                         "hidden_size": report["hidden_size"]},
              "training_status": "SMOKE_ONLY", "evaluation_status": "EVALUATION_PENDING",
              "calibration_status": "UNCALIBRATED", "activation_status": "INACTIVE",
              "model_state": "EXPERIMENTAL"}
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(register(args.model_dir, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
