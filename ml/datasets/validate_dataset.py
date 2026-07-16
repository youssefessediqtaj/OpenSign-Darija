from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {"email", "user_id", "password", "access_token", "refresh_token"}
ALLOWED_SPLITS = {"train", "validation", "test"}


def _scan_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                findings.append(child_path)
            findings.extend(_scan_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_scan_forbidden_keys(child, f"{path}[{index}]"))
    return findings


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    items = manifest.get("items", [])
    if not isinstance(items, list):
        errors.append("items must be a list")
        items = []

    forbidden = _scan_forbidden_keys(manifest)
    if forbidden:
        errors.append(f"forbidden identity keys found: {', '.join(forbidden[:10])}")

    contributor_splits: dict[str, set[str]] = defaultdict(set)
    required = {
        "contribution_id",
        "recording_id",
        "contributor_public_id",
        "sign_code",
        "split",
        "landmark_object_key",
        "checksum_landmarks",
    }
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] must be an object")
            continue
        missing = sorted(required - set(item.keys()))
        if missing:
            errors.append(f"items[{index}] missing: {', '.join(missing)}")
        split = item.get("split")
        if split not in ALLOWED_SPLITS:
            errors.append(f"items[{index}] has invalid split: {split}")
        contributor = item.get("contributor_public_id")
        if contributor:
            contributor_splits[str(contributor)].add(str(split))
        if item.get("video_object_key") and not item.get("video_consent"):
            errors.append(f"items[{index}] includes video without video_consent=true")

    leaked_contributors = {
        contributor: sorted(splits)
        for contributor, splits in contributor_splits.items()
        if len(splits) > 1
    }
    if leaked_contributors:
        errors.append("same contributor appears in multiple splits")

    if not items:
        warnings.append("manifest has no items; valid for scaffolding but not for training")

    return {"valid": not errors, "errors": errors, "warnings": warnings, "items": len(items)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a dataset manifest.")
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--report", type=Path, default=Path("artifacts/datasets/validation-report.json"))
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = validate_manifest(manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
