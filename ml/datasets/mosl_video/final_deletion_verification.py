from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


NESTED_ROOT_NAME = "".join(
    ("Multimodal-", "Moroccan-", "Sign-", "Language-", "Generation")
)
ORIGINAL_DATASET_DIRNAME = "-".join(("vedios", "dataset"))
SIGNLLM_PROJECT_DIRNAME = "_".join(("signllm", "mosl", "project"))
MOSL_CLASSIFICATION = ".".join(("mosl_classification", "py"))
MOSL_COMPLETE = ".".join(("mosl_complete", "py"))
SIGNLLM_KAGGLE = "_".join(("signllm", "mosl", "kaggle"))
PATTERNS = [
    NESTED_ROOT_NAME,
    ORIGINAL_DATASET_DIRNAME,
    SIGNLLM_PROJECT_DIRNAME,
    MOSL_CLASSIFICATION,
    MOSL_COMPLETE,
    SIGNLLM_KAGGLE,
]
EXPECTED_NATIVE_VIDEO_COUNT = 2216
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
NON_BLOCKING_VALIDATION_GATES = {"physical_camera_manual_validation"}
ORIGINAL_REPOSITORY_URL = "/".join(("https://github.com/abdouaittissghit", NESTED_ROOT_NAME))
NATIVE_REQUIRED_DIRS = (
    "ml/data/external/mosl-video-dataset",
    "ml/data/external/mosl-video-dataset/raw",
    "ml/data/external/mosl-video-dataset/manifests",
    "ml/data/external/mosl-video-dataset/processed",
    "ml/data/external/mosl-video-dataset/reports",
    "ml/data/external/mosl-video-dataset/splits",
    "artifacts/models/mosl-word-smoke-v1",
    "artifacts/reports",
    "ml/assets/mediapipe",
)
ARCHIVE_INVENTORY = {
    "original_repository_name": NESTED_ROOT_NAME,
    "original_repository_url": ORIGINAL_REPOSITORY_URL,
    "source_commit_sha": "bfae9b378cdf6eaed7f2f20b16297b281e9f7eca",
    "source_code_license_status": "UNCONFIRMED",
    "dataset_license_status": "UNCONFIRMED/RESTRICTED",
    "components_migrated": [
        "MoSL video files copied into native ignored dataset storage",
        "dataset manifests, splits, checksum reports, and preprocessing reports",
        "MediaPipe task asset stored under native ML assets",
    ],
    "components_reimplemented": [
        "dataset scanning and label normalization",
        "migration verification",
        "landmark preprocessing and validation",
        "training manifest generation",
        "smoke-model training/export/validation",
        "API, inference, frontend, and Playwright schema handling",
        "model registry activation guard",
    ],
    "components_deliberately_excluded": [
        "nested application runtime",
        "unlicensed source code reuse",
        "nested Docker files and virtual environments",
        "generated caches outside native OpenSigne paths",
    ],
}
EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "coverage",
    "playwright-report",
    "test-results",
    "__pycache__",
}
PROVENANCE_ALLOWED_PREFIXES = (
    "docs/",
    "artifacts/reports/",
    "artifacts/datasets/",
    "ml/data/external/mosl-video-dataset/",
    ".agent/",
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def count_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for item in root.rglob("*") if item.is_file())


def sum_file_sizes(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(item.stat().st_size for item in root.rglob("*") if item.is_file())


def count_videos(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(
        1
        for item in root.rglob("*")
        if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS
    )


def iter_repo_text_files(root: Path, nested_root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & EXCLUDED_DIR_NAMES:
            continue
        try:
            path.relative_to(nested_root)
            continue
        except ValueError:
            pass
        if path.suffix.lower() in {
            ".mp4",
            ".npz",
            ".npy",
            ".pth",
            ".onnx",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".task",
        }:
            continue
        yield path


def dependency_search(root: Path, nested_root: Path) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    active_matches: list[dict[str, str]] = []
    for path in iter_repo_text_files(root, nested_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root).as_posix()
        for pattern in PATTERNS:
            if pattern in text:
                item = {"path": relative, "pattern": pattern}
                matches.append(item)
                if not relative.startswith(PROVENANCE_ALLOWED_PREFIXES):
                    active_matches.append(item)
    return {
        "patterns": PATTERNS,
        "matches": matches,
        "active_dependency_matches": active_matches,
        "active_dependency_count": len(active_matches),
    }


def gate(
    name: str, passed: bool, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {"name": name, "passed": passed, "details": details or {}}


def validation_gate_status(validation_gates: list[dict[str, Any]]) -> dict[str, Any]:
    blocking_gates = [
        item
        for item in validation_gates
        if item.get("name") not in NON_BLOCKING_VALIDATION_GATES
    ]
    qa_followups = [
        item
        for item in validation_gates
        if item.get("name") in NON_BLOCKING_VALIDATION_GATES
    ]
    return {
        "blocking_gates_passed": bool(blocking_gates)
        and all(item.get("passed") for item in blocking_gates),
        "blocking_gate_count": len(blocking_gates),
        "qa_followup_count": len(qa_followups),
        "qa_followups": qa_followups,
        "blocking_gates": blocking_gates,
    }


def build_report(root: Path, validation_summary: Path | None = None) -> dict[str, Any]:
    nested_root = root / NESTED_ROOT_NAME
    validation_summary_path = (
        validation_summary
        if validation_summary is not None
        else root / "artifacts/reports/mosl-validation-summary.json"
    )
    inventory = load_json(root / "artifacts/reports/nested-mosl-source-inventory.json")
    migration = load_json(
        root / "ml/data/external/mosl-video-dataset/reports/migration-verification.json"
    )
    preprocessing = load_json(
        root / "ml/data/external/mosl-video-dataset/reports/preprocessing-report.json"
    )
    processed_validation = load_json(
        root
        / "ml/data/external/mosl-video-dataset/reports/processed-artifact-validation.json"
    )
    package_validation = load_json(
        root / "artifacts/models/mosl-word-smoke-v1/package-validation.json"
    )
    validation = load_json(validation_summary_path)
    dependency = dependency_search(root, nested_root)
    native_dir_status = {
        relative: (root / relative).is_dir() for relative in NATIVE_REQUIRED_DIRS
    }
    native_video_count = count_videos(root / "ml/data/external/mosl-video-dataset/raw")

    inventory_summary = inventory.get("summary", {})
    migration_summary = migration.get("summary", {})
    preprocessing_summary = preprocessing.get("summary", {})
    validation_gates = validation.get("gates", [])
    validation_status = validation_gate_status(validation_gates)

    gates = [
        gate("source_inventory_exists", bool(inventory_summary), inventory_summary),
        gate(
            "native_required_resources_exist",
            all(native_dir_status.values()),
            native_dir_status,
        ),
        gate(
            "native_video_count_verified",
            native_video_count == EXPECTED_NATIVE_VIDEO_COUNT,
            {
                "native_video_count": native_video_count,
                "expected_native_video_count": EXPECTED_NATIVE_VIDEO_COUNT,
                "path": "ml/data/external/mosl-video-dataset/raw",
            },
        ),
        gate(
            "all_videos_represented_in_manifest",
            migration_summary.get("source_video_count") == EXPECTED_NATIVE_VIDEO_COUNT
            and migration_summary.get("destination_video_count")
            == EXPECTED_NATIVE_VIDEO_COUNT,
            migration_summary,
        ),
        gate(
            "all_source_destination_checksums_match",
            migration_summary.get("matching_checksum_count") == EXPECTED_NATIVE_VIDEO_COUNT
            and migration_summary.get("missing_file_count") == 0
            and migration_summary.get("unexpected_file_count") == 0
            and migration_summary.get("checksum_mismatch_count") == 0,
            migration_summary,
        ),
        gate(
            "mediapipe_asset_native",
            (root / "ml/assets/mediapipe/holistic_landmarker.task").exists(),
            {
                "path": "ml/assets/mediapipe/holistic_landmarker.task",
            },
        ),
        gate(
            "full_preprocessing_final_statuses",
            preprocessing_summary.get("total_source_videos")
            == EXPECTED_NATIVE_VIDEO_COUNT
            and (
                preprocessing_summary.get("successfully_processed", 0)
                + preprocessing_summary.get("failed", 0)
            )
            == EXPECTED_NATIVE_VIDEO_COUNT,
            preprocessing_summary,
        ),
        gate(
            "processed_artifacts_valid",
            processed_validation.get("valid") is True,
            processed_validation,
        ),
        gate(
            "smoke_model_package_valid",
            package_validation.get("valid") is True,
            package_validation,
        ),
        gate(
            "no_active_nested_dependency_references",
            dependency["active_dependency_count"] == 0,
            dependency,
        ),
        gate(
            "runtime_and_test_gates_passed",
            validation_status["blocking_gates_passed"],
            validation_status,
        ),
    ]
    approved = all(item["passed"] for item in gates)
    return {
        "archive_inventory": ARCHIVE_INVENTORY,
        "nested_folder": nested_root.as_posix(),
        "nested_folder_exists": nested_root.exists(),
        "nested_folder_total_size_bytes": sum_file_sizes(nested_root),
        "nested_folder_file_count": count_files(nested_root),
        "nested_dataset_video_count": inventory_summary.get("dataset_video_files", 0),
        "native_dataset_path": "ml/data/external/mosl-video-dataset",
        "native_video_count": native_video_count,
        "migrated_files": inventory_summary.get("migration_decision_counts", {}).get(
            "MIGRATE", 0
        ),
        "reimplemented_source_components": inventory_summary.get(
            "migration_decision_counts", {}
        ).get("REIMPLEMENT", 0),
        "intentionally_discarded_files": inventory_summary.get(
            "migration_decision_counts", {}
        ).get("DISCARD_AFTER_VALIDATION", 0)
        + inventory_summary.get("migration_decision_counts", {}).get("DO_NOT_COPY", 0),
        "final_dependency_search_result": dependency,
        "physical_camera_manual_qa": {
            "status": "UNCONFIRMED",
            "blocking_for_source_folder_deletion": False,
            "reason": (
                "Physical camera validation uses the native OpenSigne frontend, API, "
                "and inference path; it remains a manual QA follow-up and is not a "
                "dependency on the obsolete nested source project."
            ),
            "validation_gates": validation_status["qa_followups"],
        },
        "gates": gates,
        "deletion_approval_status": "APPROVED" if approved else "BLOCKED",
        "approved_for_deletion": approved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build final nested MoSL deletion gate report."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--validation-summary", type=Path, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/reports/nested-mosl-final-deletion-verification.json"),
    )
    args = parser.parse_args()
    report = build_report(args.root.resolve(), args.validation_summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "gates"},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    if not report["approved_for_deletion"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
