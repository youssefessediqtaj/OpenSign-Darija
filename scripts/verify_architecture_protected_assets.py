#!/usr/bin/env python3
"""Snapshot and compare assets protected by the architecture-refactor contract.

Run with the inference virtualenv because canonical-output verification deliberately
uses the same NumPy and ONNX Runtime family as the production inference service.
The script reads data/model assets only and writes one architecture audit report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "ml" / "data" / "external" / "mosl-video-dataset"
MODEL_ROOT = ROOT / "artifacts" / "models" / "mosl-isolated-sign-v1"
REPORT_PATH = ROOT / "artifacts" / "reports" / "architecture-refactor-protected-assets.json"
CANONICAL_FIXTURE = (
    DATASET_ROOT
    / "processed"
    / "landmarks"
    / "9887333505c8b7a2b006ad55a9209c0943f0f58f712663f6c5445e30f9c7ceed.npz"
)
PROTECTED_PATHS = [
    "ml/data/external/mosl-video-dataset/",
    "ml/assets/mediapipe/",
    "artifacts/models/mosl-isolated-sign-v1/",
    "artifacts/reports/",
    "docs/reports/",
]
REFACTOR_STARTED_AT = datetime(2026, 7, 23, 19, 5, tzinfo=UTC).timestamp()
PREEXISTING_ARTIFACT_REPORT_COUNT = 28
ADDITIVE_ARTIFACT_REPORTS = {
    "architecture-refactor-final-report.json",
    "architecture-refactor-protected-assets.json",
    "module-dependency-graph.json",
    "pre-architecture-refactor-baseline.json",
    "repository-file-inventory.csv",
    "repository-file-inventory.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_snapshot(root: Path) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    tree_digest = hashlib.sha256()
    if root.exists():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(root).as_posix()
            digest = sha256(path)
            size = path.stat().st_size
            files[relative] = {"sha256": digest, "size_bytes": size}
            tree_digest.update(relative.encode("utf-8"))
            tree_digest.update(b"\0")
            tree_digest.update(digest.encode("ascii"))
            tree_digest.update(b"\0")
    return {
        "file_count": len(files),
        "tree_sha256": tree_digest.hexdigest(),
        "files": files,
    }


def artifact_reports_audit() -> dict[str, Any]:
    root = ROOT / "artifacts" / "reports"
    files = sorted(path for path in root.rglob("*") if path.is_file())
    changed_during_refactor = {
        path.relative_to(root).as_posix()
        for path in files
        if path.stat().st_mtime >= REFACTOR_STARTED_AT
    }
    unexpected = sorted(changed_during_refactor - ADDITIVE_ARTIFACT_REPORTS)
    additive_present = sorted(changed_during_refactor & ADDITIVE_ARTIFACT_REPORTS)
    expected_total = PREEXISTING_ARTIFACT_REPORT_COUNT + len(additive_present)
    return {
        "method": (
            "The pre-refactor inventory recorded 33 files after five additive audit "
            "reports existed, establishing 28 preexisting files. Modification times "
            "must show only the allowlisted additive reports changed since refactor start."
        ),
        "preexisting_file_count": PREEXISTING_ARTIFACT_REPORT_COUNT,
        "current_file_count": len(files),
        "additive_paths_present": additive_present,
        "unexpected_new_or_modified_paths": unexpected,
        "expected_current_file_count": expected_total,
        "preexisting_reports_preserved_and_changes_additive_only": (
            not unexpected and len(files) == expected_total
        ),
    }


def validate_raw_dataset() -> dict[str, Any]:
    manifest_path = DATASET_ROOT / "manifests" / "videos.jsonl"
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    aggregate = hashlib.sha256()
    missing: list[str] = []
    checksum_mismatches: list[str] = []
    size_mismatches: list[str] = []
    for record in records:
        relative = str(record["current_relative_path"])
        path = DATASET_ROOT / relative
        if not path.is_file():
            missing.append(relative)
            continue
        actual_size = path.stat().st_size
        if actual_size != int(record["size_bytes"]):
            size_mismatches.append(relative)
        actual_digest = sha256(path)
        if actual_digest != record["sha256"]:
            checksum_mismatches.append(relative)
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(actual_digest.encode("ascii"))
        aggregate.update(b"\0")
    return {
        "manifest_sha256": sha256(manifest_path),
        "record_count": len(records),
        "verified_file_count": len(records) - len(missing),
        "missing": missing,
        "size_mismatches": size_mismatches,
        "checksum_mismatches": checksum_mismatches,
        "all_manifest_records_match_raw_files": not (
            missing or size_mismatches or checksum_mismatches
        ),
        "raw_tree_from_manifest_sha256": aggregate.hexdigest(),
    }


def canonical_inference() -> dict[str, Any]:
    labels = json.loads((MODEL_ROOT / "labels.json").read_text(encoding="utf-8"))
    calibration = json.loads(
        (MODEL_ROOT / "confidence-calibration.json").read_text(encoding="utf-8")
    )
    with np.load(CANONICAL_FIXTURE) as payload:
        landmarks = np.asarray(payload["landmarks"], dtype=np.float32)
    batch = landmarks[np.newaxis, ...]
    session = ort.InferenceSession(
        str(MODEL_ROOT / "model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    model_input = session.get_inputs()[0]
    model_output = session.get_outputs()[0]
    logits = np.asarray(
        session.run([model_output.name], {model_input.name: batch})[0][0],
        dtype=np.float32,
    )
    temperature = float(calibration["temperature"])
    scaled = logits / temperature
    scaled -= np.max(scaled)
    probabilities = np.exp(scaled)
    probabilities /= probabilities.sum()
    ranking = np.argsort(-probabilities)
    top_index = int(ranking[0])
    second_index = int(ranking[1])
    top_probability = float(probabilities[top_index])
    margin = float(probabilities[top_index] - probabilities[second_index])
    accepted = (
        top_probability >= float(calibration["unknown_threshold"])
        and margin >= float(calibration["margin_threshold"])
    )
    return {
        "fixture": CANONICAL_FIXTURE.relative_to(ROOT).as_posix(),
        "fixture_sha256": sha256(CANONICAL_FIXTURE),
        "input_name": model_input.name,
        "input_shape": list(model_input.shape),
        "input_dtype": model_input.type,
        "output_name": model_output.name,
        "output_shape": list(model_output.shape),
        "output_dtype": model_output.type,
        "labels": labels,
        "raw_logits": [float(value) for value in logits],
        "probabilities": [float(value) for value in probabilities],
        "ranked_labels": [labels[int(index)] for index in ranking],
        "top_label": labels[top_index],
        "top_probability": top_probability,
        "margin": margin,
        "accepted": accepted,
    }


def snapshot() -> dict[str, Any]:
    checksums_path = MODEL_ROOT / "checksums.json"
    checksums_manifest = json.loads(checksums_path.read_text(encoding="utf-8"))
    actual_checksums = {
        name: sha256(MODEL_ROOT / name)
        for name in sorted(checksums_manifest)
        if (MODEL_ROOT / name).is_file()
    }
    labels = json.loads((MODEL_ROOT / "labels.json").read_text(encoding="utf-8"))
    landmark_schema = json.loads(
        (MODEL_ROOT / "landmark-schema.json").read_text(encoding="utf-8")
    )
    package_validation = json.loads(
        (MODEL_ROOT / "package-validation.json").read_text(encoding="utf-8")
    )
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "active_model": {
            "name": "mosl-isolated-sign-v1",
            "version": "1.0.0",
            "onnx_sha256": sha256(MODEL_ROOT / "model.onnx"),
            "checksum_manifest_sha256": sha256(checksums_path),
            "checksum_manifest_matches_files": actual_checksums == checksums_manifest,
            "declared_file_checksums": checksums_manifest,
            "actual_file_checksums": actual_checksums,
            "package_tree": tree_snapshot(MODEL_ROOT),
            "supported_sign_labels": labels,
            "input_tensor_shape": landmark_schema["input_shape"],
            "output_tensor_shape": package_validation["runtime"]["output_shape"],
        },
        "dataset": validate_raw_dataset(),
        "processed_landmark_cache": tree_snapshot(DATASET_ROOT / "processed"),
        "mediapipe_assets": tree_snapshot(ROOT / "ml" / "assets" / "mediapipe"),
        "artifact_reports": artifact_reports_audit(),
        "existing_architecture_reports": tree_snapshot(ROOT / "docs" / "reports"),
        "canonical_inference": canonical_inference(),
    }


def comparison(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    keys = {
        "onnx_sha256_unchanged": (
            before["active_model"]["onnx_sha256"]
            == after["active_model"]["onnx_sha256"]
        ),
        "model_checksum_manifest_unchanged": (
            before["active_model"]["checksum_manifest_sha256"]
            == after["active_model"]["checksum_manifest_sha256"]
        ),
        "model_package_tree_unchanged": (
            before["active_model"]["package_tree"]["tree_sha256"]
            == after["active_model"]["package_tree"]["tree_sha256"]
        ),
        "labels_unchanged": (
            before["active_model"]["supported_sign_labels"]
            == after["active_model"]["supported_sign_labels"]
        ),
        "input_shape_unchanged": (
            before["active_model"]["input_tensor_shape"]
            == after["active_model"]["input_tensor_shape"]
        ),
        "output_shape_unchanged": (
            before["active_model"]["output_tensor_shape"]
            == after["active_model"]["output_tensor_shape"]
        ),
        "dataset_manifest_unchanged": (
            before["dataset"]["manifest_sha256"] == after["dataset"]["manifest_sha256"]
        ),
        "dataset_raw_files_unchanged": (
            before["dataset"]["raw_tree_from_manifest_sha256"]
            == after["dataset"]["raw_tree_from_manifest_sha256"]
        ),
        "processed_cache_unchanged": (
            before["processed_landmark_cache"]["tree_sha256"]
            == after["processed_landmark_cache"]["tree_sha256"]
        ),
        "mediapipe_assets_unchanged": (
            before["mediapipe_assets"]["tree_sha256"]
            == after["mediapipe_assets"]["tree_sha256"]
        ),
        "canonical_logits_unchanged": (
            before["canonical_inference"]["raw_logits"]
            == after["canonical_inference"]["raw_logits"]
        ),
        "canonical_probabilities_unchanged": (
            before["canonical_inference"]["probabilities"]
            == after["canonical_inference"]["probabilities"]
        ),
        "canonical_decision_unchanged": (
            before["canonical_inference"]["top_label"]
            == after["canonical_inference"]["top_label"]
            and before["canonical_inference"]["accepted"]
            == after["canonical_inference"]["accepted"]
        ),
        "preexisting_docs_reports_unchanged": (
            all(
                after["existing_architecture_reports"]["files"].get(relative)
                == metadata
                for relative, metadata in before["existing_architecture_reports"][
                    "files"
                ].items()
            )
        ),
        "artifact_reports_additive_only": after["artifact_reports"][
            "preexisting_reports_preserved_and_changes_additive_only"
        ],
    }
    return {
        **keys,
        "all_protected_assets_and_outputs_unchanged": all(keys.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    args = parser.parse_args()
    current = snapshot()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.phase == "before":
        report = {
            "schema_version": "OPEN_SIGNE_ARCHITECTURE_PROTECTED_ASSETS_V1",
            "protected_paths": PROTECTED_PATHS,
            "policy": (
                "No protected data/model/report asset is deleted, renamed, regenerated, or moved. "
                "New architecture audit reports are additive."
            ),
            "before_refactor": current,
            "after_refactor": None,
            "comparison": None,
        }
    else:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        before = report["before_refactor"]
        report["after_refactor"] = current
        report["comparison"] = comparison(before, current)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summary = {
        "phase": args.phase,
        "onnx_sha256": current["active_model"]["onnx_sha256"],
        "dataset_manifest_sha256": current["dataset"]["manifest_sha256"],
        "dataset_records": current["dataset"]["record_count"],
        "model_package_valid": current["active_model"]["checksum_manifest_matches_files"],
        "dataset_valid": current["dataset"]["all_manifest_records_match_raw_files"],
        "canonical_top_label": current["canonical_inference"]["top_label"],
        "canonical_accepted": current["canonical_inference"]["accepted"],
    }
    if args.phase == "after":
        summary["all_unchanged"] = report["comparison"][
            "all_protected_assets_and_outputs_unchanged"
        ]
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
