from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
SOURCE_SUFFIXES = {".py", ".ipynb", ".yaml", ".yml", ".json", ".md", ".txt", ".toml"}
GENERATED_SUFFIXES = {".npy", ".npz", ".pth", ".pt", ".png", ".log", ".pid", ".pyc"}
SOURCE_ROOT_NAME = "".join(
    ("Multimodal-", "Moroccan-", "Sign-", "Language-", "Generation")
)
ORIGINAL_DATASET_DIRNAME = "-".join(("vedios", "dataset"))
SIGNLLM_PROJECT_DIRNAME = "_".join(("signllm", "mosl", "project"))
SOURCE_COMPONENT_FILENAMES = {
    ".".join(("mosl_classification", "py")),
    ".".join(("mosl_complete", "py")),
    ".".join(("_".join(("signllm", "mosl", "kaggle")), "py")),
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in {".py"}:
        return "python"
    if suffix == ".ipynb":
        return "notebook"
    if suffix in {".md", ".txt"}:
        return "document"
    if suffix in {".yaml", ".yml", ".json", ".toml"}:
        return "configuration"
    if suffix in {".png", ".jpg", ".jpeg", ".gif"}:
        return "image"
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".pth", ".pt", ".onnx", ".npy", ".npz"}:
        return "model_or_array_artifact"
    if path.name.startswith("."):
        return "hidden"
    return suffix.lstrip(".") or "unknown"


def classify(relative_path: Path) -> dict[str, Any]:
    parts = relative_path.parts
    suffix = relative_path.suffix.lower()
    is_virtual_environment = ".venv" in parts
    is_dataset_content = (
        parts[:1] == (ORIGINAL_DATASET_DIRNAME,) and suffix in VIDEO_SUFFIXES
    )
    is_generated_output = (
        "outputs" in parts
        or "output" in parts
        or "__pycache__" in parts
        or suffix in GENERATED_SUFFIXES
    )
    is_source_code = suffix in SOURCE_SUFFIXES or relative_path.name in {
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
    }

    if ".git" in parts:
        return {
            "is_source_code": False,
            "is_dataset_content": False,
            "is_generated_output": False,
            "is_virtual_environment": False,
            "migration_decision": "DO_NOT_COPY",
            "target_path": "",
            "reason": "Nested Git metadata is not part of the native OpenSigne application.",
        }
    if is_virtual_environment:
        return {
            "is_source_code": False,
            "is_dataset_content": False,
            "is_generated_output": True,
            "is_virtual_environment": True,
            "migration_decision": "DO_NOT_COPY",
            "target_path": "",
            "reason": "Nested virtual-environment dependency payload must not be copied.",
        }
    if is_dataset_content:
        native_tail = Path(*parts[1:])
        return {
            "is_source_code": False,
            "is_dataset_content": True,
            "is_generated_output": False,
            "is_virtual_environment": False,
            "migration_decision": "MIGRATE",
            "target_path": f"ml/data/external/mosl-video-dataset/raw/{native_tail.as_posix()}",
            "reason": "Raw MoSL video is migrated with Unicode filename and checksum preserved.",
        }
    if parts[:1] == (ORIGINAL_DATASET_DIRNAME,):
        return {
            "is_source_code": False,
            "is_dataset_content": False,
            "is_generated_output": True,
            "is_virtual_environment": False,
            "migration_decision": "DISCARD_AFTER_VALIDATION",
            "target_path": "",
            "reason": "Non-video dataset-side temporary file is not required after video checksums match.",
        }
    if "__pycache__" in parts or suffix == ".pyc":
        return {
            "is_source_code": False,
            "is_dataset_content": False,
            "is_generated_output": True,
            "is_virtual_environment": False,
            "migration_decision": "DO_NOT_COPY",
            "target_path": "",
            "reason": "Compiled Python cache has no source or runtime value.",
        }
    if is_generated_output:
        return {
            "is_source_code": False,
            "is_dataset_content": False,
            "is_generated_output": True,
            "is_virtual_environment": False,
            "migration_decision": "DISCARD_AFTER_VALIDATION",
            "target_path": "",
            "reason": "Generated research outputs/checkpoints are superseded by native OpenSigne reports and smoke artifacts.",
        }
    if suffix == ".pdf" or suffix == ".ipynb":
        return {
            "is_source_code": suffix == ".ipynb",
            "is_dataset_content": False,
            "is_generated_output": False,
            "is_virtual_environment": False,
            "migration_decision": "DOCUMENT_ONLY",
            "target_path": "docs/integrations/mosl-source-audit.md",
            "reason": "Research reference retained as provenance, not as active runtime code.",
        }
    if suffix == ".py":
        if (
            SIGNLLM_PROJECT_DIRNAME in parts
            or relative_path.name in SOURCE_COMPONENT_FILENAMES
        ):
            return {
                "is_source_code": True,
                "is_dataset_content": False,
                "is_generated_output": False,
                "is_virtual_environment": False,
                "migration_decision": "REIMPLEMENT",
                "target_path": "ml/datasets/mosl_video/, ml/preprocessing/, ml/training/",
                "reason": "Useful parsing/preprocessing/training behavior is represented by native clean-room modules because source-code license is unconfirmed.",
            }
    if relative_path.name in {
        "Dockerfile",
        "docker-compose.yml",
        "docker-entrypoint.sh",
        "requirements.txt",
    }:
        return {
            "is_source_code": is_source_code,
            "is_dataset_content": False,
            "is_generated_output": False,
            "is_virtual_environment": False,
            "migration_decision": "DISCARD_AFTER_VALIDATION",
            "target_path": "",
            "reason": "Duplicate nested application infrastructure is replaced by root OpenSigne Docker and dependency files.",
        }
    if parts[:1] in {(".agent",), (".devcontainer",)}:
        return {
            "is_source_code": is_source_code,
            "is_dataset_content": False,
            "is_generated_output": False,
            "is_virtual_environment": False,
            "migration_decision": "DISCARD_AFTER_VALIDATION",
            "target_path": "",
            "reason": "Nested local agent/devcontainer files do not belong to the native application.",
        }
    return {
        "is_source_code": is_source_code,
        "is_dataset_content": False,
        "is_generated_output": False,
        "is_virtual_environment": False,
        "migration_decision": "DOCUMENT_ONLY"
        if is_source_code
        else "DISCARD_AFTER_VALIDATION",
        "target_path": "docs/integrations/mosl-source-audit.md"
        if is_source_code
        else "",
        "reason": "Retained only as migration provenance; no active native runtime dependency.",
    }


def build_inventory(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(
        (item for item in source_root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(source_root).as_posix(),
    ):
        relative = path.relative_to(source_root)
        classification = classify(relative)
        checksum = sha256_file(path)
        record = {
            "relative_path": relative.as_posix(),
            "file_type": file_type(path),
            "file_size_bytes": path.stat().st_size,
            "sha256": checksum,
            **classification,
            "duplicate": False,
        }
        records.append(record)

    checksum_counts = Counter(str(record["sha256"]) for record in records)
    for record in records:
        record["duplicate"] = checksum_counts[str(record["sha256"])] > 1

    decisions = Counter(str(record["migration_decision"]) for record in records)
    file_types = Counter(str(record["file_type"]) for record in records)
    summary = {
        "source_root": source_root.as_posix(),
        "total_files": len(records),
        "total_size_bytes": sum(int(record["file_size_bytes"]) for record in records),
        "dataset_video_files": sum(
            1 for record in records if record["is_dataset_content"]
        ),
        "virtual_environment_files": sum(
            1 for record in records if record["is_virtual_environment"]
        ),
        "generated_output_files": sum(
            1 for record in records if record["is_generated_output"]
        ),
        "source_code_or_document_files": sum(
            1 for record in records if record["is_source_code"]
        ),
        "duplicate_file_records": sum(1 for record in records if record["duplicate"]),
        "unique_checksum_count": len(checksum_counts),
        "migration_decision_counts": dict(sorted(decisions.items())),
        "file_type_counts": dict(sorted(file_types.items())),
    }
    return {"summary": summary, "items": records}


def write_inventory(report: dict[str, Any], json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fieldnames = [
        "relative_path",
        "file_type",
        "file_size_bytes",
        "sha256",
        "is_source_code",
        "is_dataset_content",
        "is_generated_output",
        "is_virtual_environment",
        "duplicate",
        "migration_decision",
        "target_path",
        "reason",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report["items"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory the nested MoSL research project."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(SOURCE_ROOT_NAME),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("artifacts/reports/nested-mosl-source-inventory.json"),
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("artifacts/reports/nested-mosl-source-inventory.csv"),
    )
    args = parser.parse_args()
    report = build_inventory(args.source_root)
    write_inventory(report, args.json_output, args.csv_output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
