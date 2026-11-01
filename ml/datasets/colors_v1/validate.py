"""Validate private color-video metadata without copying or changing source media."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SUPPORTED = {".mp4", ".mov", ".webm"}
SOURCE_TYPES = {"source_reference_video", "original_recording", "synthetic_character_replacement", "augmented_recording", "unknown"}
REVIEWS = {"PENDING_REVIEW", "APPROVED", "REJECTED"}
SPLITS = {"train", "validation", "test", "unassigned"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_video(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
         "stream=codec_name,width,height,avg_frame_rate,duration,nb_read_frames:format=duration,format_name", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=20,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("no video stream")
    video = streams[0]
    width, height = int(video.get("width", 0)), int(video.get("height", 0))
    numerator, denominator = str(video.get("avg_frame_rate", "0/1")).split("/")
    fps = float(numerator) / float(denominator)
    duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)
    if width <= 0 or height <= 0 or fps <= 0 or duration <= 0:
        raise ValueError("invalid video dimensions, duration, or frame rate")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
                    "-f", "null", "-"], check=True, capture_output=True, timeout=60)
    return {"duration_seconds": duration, "fps": fps, "width": width, "height": height,
            "codec": video.get("codec_name"), "container": data.get("format", {}).get("format_name"),
            "readable_frames": int(video.get("nb_read_frames", 0))}


def _contained_file(root: Path, raw: Any) -> Path:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
        raise ValueError("file_path must be a relative path")
    candidate = root / raw
    if any(part == ".." for part in Path(raw).parts):
        raise ValueError("file_path must not traverse directories")
    for parent in [candidate, *candidate.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("symlinks are not accepted")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("file missing or outside import directory")
    return resolved


def validate(config: dict[str, Any], records: Any, root: Path, *, inspect_media: bool = True) -> dict[str, Any]:
    """Return evidence and blockers; never use legacy data as an implicit input."""
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[dict[str, Any]] = []
    root = root.resolve()
    legacy = (Path(__file__).resolve().parents[2] / "data/external/mosl-video-dataset").resolve()
    if root == legacy or root.is_relative_to(legacy) or legacy.is_relative_to(root):
        raise ValueError("video root must be isolated from the legacy dataset")
    if config.get("dataset_id") != "colors_v1":
        errors.append("dataset_id must be colors_v1")
    labels: dict[str, dict[str, Any]] = {}
    variants: dict[str, str] = {}
    configured_labels = config.get("labels", [])
    if not isinstance(configured_labels, list):
        configured_labels = []
        errors.append("labels must be a list")
    for label in configured_labels:
        if not isinstance(label, dict) or not isinstance(label.get("variants"), list):
            errors.append("label must be an object with a variants list")
            continue
        label_id = label.get("id")
        if not isinstance(label_id, str) or not label_id or label_id in labels:
            errors.append("label IDs must be unique nonempty strings")
            continue
        labels[label_id] = label
        for variant in label.get("variants", []):
            if not isinstance(variant, str) or not variant or variant in variants:
                errors.append(f"duplicate or invalid variant: {variant}")
            else:
                variants[variant] = label_id
    if not isinstance(records, list):
        records = []
        errors.append("manifest must be a JSON array")
    ids: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    referenced: set[Path] = set()
    for index, item in enumerate(records):
        prefix = f"record {index + 1}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: expected object")
            continue
        video_id = item.get("video_id")
        if not isinstance(video_id, str) or not video_id or video_id in ids:
            errors.append(f"{prefix}: missing or duplicate video_id")
            continue
        ids[video_id] = item
        prefix = f"{video_id}"
        label_id, variant = item.get("semantic_label"), item.get("sign_variant_id")
        if not isinstance(label_id, str) or not isinstance(variant, str):
            errors.append(f"{prefix}: label and variant must be strings")
        elif label_id not in labels or variants.get(variant) != label_id:
            errors.append(f"{prefix}: unknown label or mismatched variant")
        elif labels[label_id].get("status") == "placeholder":
            errors.append(f"{prefix}: placeholder labels cannot be used for data")
        if not isinstance(item.get("source_type"), str) or item.get("source_type") not in SOURCE_TYPES:
            errors.append(f"{prefix}: invalid source_type")
        if not isinstance(item.get("linguistic_review_status"), str) or item.get("linguistic_review_status") not in REVIEWS:
            errors.append(f"{prefix}: invalid linguistic_review_status")
        if not isinstance(item.get("split", "unassigned"), str) or item.get("split", "unassigned") not in SPLITS:
            errors.append(f"{prefix}: invalid split")
        for field in ("lineage_group_id", "license", "consent_status", "provenance"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{prefix}: missing {field}")
        if not isinstance(item.get("consent_status"), str) or item.get("consent_status") not in {"approved", "pending", "denied", "not_applicable"}:
            errors.append(f"{prefix}: invalid consent_status")
        if item.get("source_type") in ("synthetic_character_replacement", "augmented_recording"):
            if not item.get("source_video_id") or not item.get("transformation_type"):
                errors.append(f"{prefix}: derived video requires parent and transformation")
        if not item.get("signer_id"):
            warnings.append(f"{prefix}: independent signer identity unknown")
        try:
            path = _contained_file(root, item.get("file_path"))
            if path.suffix.lower() not in SUPPORTED:
                raise ValueError("unsupported video extension")
            referenced.add(path)
            digest = sha256(path)
            if digest in hashes:
                errors.append(f"{prefix}: duplicate bytes with {hashes[digest]}")
            hashes[digest] = video_id
            claimed = item.get("file_hash")
            if claimed and claimed != digest:
                errors.append(f"{prefix}: file_hash does not match file")
            media = probe_video(path) if inspect_media else {}
            checked.append({**item, "file_hash": digest, **media})
        except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            errors.append(f"{prefix}: invalid media ({type(exc).__name__}: {exc})")
    for video_id, item in ids.items():
        parent_id = item.get("source_video_id")
        if parent_id is not None and not isinstance(parent_id, str):
            errors.append(f"{video_id}: source_video_id must be a string")
            continue
        if parent_id:
            parent = ids.get(parent_id)
            if not parent or parent_id == video_id:
                errors.append(f"{video_id}: invalid parent reference")
            elif (parent.get("lineage_group_id") != item.get("lineage_group_id") or
                  parent.get("semantic_label") != item.get("semantic_label") or
                  parent.get("sign_variant_id") != item.get("sign_variant_id")):
                errors.append(f"{video_id}: parent label, variant, or lineage differs")
            seen = {video_id}
            while parent_id and parent_id in ids:
                if parent_id in seen:
                    errors.append(f"{video_id}: cyclic source lineage")
                    break
                seen.add(parent_id)
                parent_id = ids[parent_id].get("source_video_id")
                if parent_id is not None and not isinstance(parent_id, str):
                    errors.append(f"{video_id}: invalid ancestor reference")
                    break
    for field in ("lineage_group_id", "signer_id"):
        assignments: dict[str, set[str]] = defaultdict(set)
        for item in ids.values():
            value, split = item.get(field), item.get("split", "unassigned")
            if isinstance(value, str) and value and isinstance(split, str) and split != "unassigned":
                assignments[str(value)].add(str(split))
        for value, splits in assignments.items():
            if len(splits) > 1:
                errors.append(f"{field} {value} crosses splits")
    if root.is_dir():
        for file in root.rglob("*"):
            if file.is_file() and not file.is_symlink() and file.suffix.lower() in SUPPORTED and file.resolve() not in referenced:
                warnings.append(f"unregistered video: {file.relative_to(root)}")
    if not records:
        warnings.append("no videos supplied")
    reviews = Counter(str(item.get("linguistic_review_status", "UNKNOWN")) for item in ids.values())
    approved = [item for item in ids.values() if item.get("linguistic_review_status") == "APPROVED"
                and item.get("consent_status") in ("approved", "not_applicable")
                and item.get("source_type") != "unknown"]
    ready = bool(checked) and len(approved) == len(ids) and not errors and inspect_media
    warnings.append("training and evaluation remain blocked until feature parity and independent splits are validated")
    return {"dataset": "colors_v1", "semantic_classes_defined": len(labels), "sign_variants_defined": len(variants),
            "total_videos": len(ids), "original_videos": sum(x.get("source_type") in ("source_reference_video", "original_recording") for x in ids.values()),
            "synthetic_videos": sum(x.get("source_type") == "synthetic_character_replacement" for x in ids.values()),
            "approved_videos": reviews["APPROVED"], "rejected_videos": reviews["REJECTED"], "pending_review": reviews["PENDING_REVIEW"],
            "declared_lineage_groups": len({x["lineage_group_id"] for x in ids.values() if isinstance(x.get("lineage_group_id"), str) and x["lineage_group_id"]}),
            "independent_source_groups": None,
            "signer_independence_verified": False, "errors": errors, "warnings": warnings,
            "media_review_ready": ready, "preprocessing_ready": False, "training_ready": False,
            "evaluation_ready": False, "records": checked}


def write_private_report(path: Path, payload: str, video_root: Path) -> None:
    """Never overwrite input or place metadata among immutable video inputs."""
    if path.resolve().is_relative_to(video_root.resolve()):
        raise ValueError("report must be outside the video root")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate COLORS_V1 private input; no videos are copied or changed")
    parser.add_argument("--config", type=Path, default=Path("ml/configs/colors_v1.json"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--video-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--split-report", type=Path,
                        help="optionally write a signer/lineage-disjoint proposed split")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not args.video_root.is_dir():
            raise ValueError("video-root must be an existing directory")
        report = validate(config, manifest, args.video_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"COLORS_V1 validation failed: {exc}", file=sys.stderr)
        return 2
    if args.split_report:
        if not report["media_review_ready"]:
            print("Split blocked: media and reviews must be ready first", file=sys.stderr)
            return 1
        from ml.datasets.colors_v1.splits import grouped_split

        try:
            proposed = grouped_split(report["records"], seed=args.seed)
        except ValueError as exc:
            print(f"Split blocked: {exc}", file=sys.stderr)
            return 1
        try:
            write_private_report(args.split_report, json.dumps(proposed, ensure_ascii=False, indent=2) + "\n", args.video_root)
        except (OSError, ValueError) as exc:
            print(f"Cannot write split report: {exc}", file=sys.stderr)
            return 2
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        try:
            write_private_report(args.report, text, args.video_root)
        except (OSError, ValueError) as exc:
            print(f"Cannot write report: {exc}", file=sys.stderr)
            return 2
    print(text)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
