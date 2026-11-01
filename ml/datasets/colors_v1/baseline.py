"""Experimental sequence-template baseline. No activation or validation is implied."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import numpy as np

from ml.datasets.colors_v1.preprocess import FEATURE_VERSION


def check_features(landmarks: np.ndarray, mask: np.ndarray) -> None:
    if landmarks.shape != (60, 75, 3) or mask.shape != (60, 75):
        raise ValueError("expected 60x75x3 landmarks and 60x75 mask")
    if not np.isfinite(landmarks).all() or not np.isfinite(mask).all():
        raise ValueError("features must be finite")
    if not np.isin(mask, [0, 1]).all():
        raise ValueError("presence mask must be binary")


def distances(landmarks: np.ndarray, mask: np.ndarray, templates: np.ndarray, masks: np.ndarray) -> np.ndarray:
    """Mean squared shared-landmark distance, giving hand landmarks extra weight."""
    weights = np.ones((75,), dtype=np.float64)
    weights[33:] = 2.0
    shared = mask[None, :, :] * masks
    weighted = shared * weights[None, None, :]
    difference = ((templates - landmarks[None, :, :, :]) ** 2).sum(axis=3)
    denominator = weighted.sum(axis=(1, 2))
    numerator = (difference * weighted).sum(axis=(1, 2))
    return np.divide(numerator, denominator, out=np.full_like(denominator, np.inf), where=denominator > 0)


def predict(model: dict[str, Any], landmarks: np.ndarray, mask: np.ndarray,
            max_distance: float | None = None, source_frame_count: int | None = None) -> dict[str, Any]:
    try:
        check_features(landmarks, mask)
    except ValueError:
        return {"status": "INFERENCE_ERROR", "semantic_label": None, "variant": None}
    if not np.any(mask[:, 33:]):
        return {"status": "NO_HAND_DETECTED", "semantic_label": None, "variant": None}
    if (source_frame_count is not None and source_frame_count < 12) or np.count_nonzero(np.any(mask[:, 33:], axis=1)) < 12:
        return {"status": "INSUFFICIENT_FRAMES", "semantic_label": None, "variant": None}
    scores = distances(landmarks, mask, model["templates"], model["masks"])
    best = int(np.argmin(scores))
    score = float(scores[best])
    if not np.isfinite(score):
        return {"status": "UNKNOWN_SIGN", "semantic_label": None, "variant": None}
    if max_distance is not None and (not np.isfinite(max_distance) or max_distance < 0):
        raise ValueError("distance threshold must be finite and nonnegative")
    accepted = max_distance is not None and score <= max_distance
    return {"status": "RECOGNIZED_COLOR" if accepted else "UNKNOWN_SIGN",
            "semantic_label": str(model["labels"][best]) if accepted else None,
            "variant": str(model["variants"][best]) if accepted else None,
            "diagnostic_candidate": str(model["labels"][best]), "distance": score,
            "calibrated": False}


def predict_from_package(path: Path, landmarks: np.ndarray, mask: np.ndarray,
                         max_distance: float | None = None, source_frame_count: int | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "MODEL_NOT_READY", "semantic_label": None, "variant": None}
    try:
        model = load(path)
    except (OSError, ValueError, KeyError):
        return {"status": "INFERENCE_ERROR", "semantic_label": None, "variant": None}
    return predict(model, landmarks, mask, max_distance, source_frame_count)


def fit(manifest: Path, feature_dir: Path, output: Path, *, allow_pending_review: bool = False) -> dict[str, Any]:
    """Build a private, explicitly experimental template package from authorized sources."""
    raw = manifest.read_bytes()
    records = json.loads(raw)
    if not isinstance(records, list) or not records:
        raise ValueError("manifest must contain source records")
    config_path = Path(__file__).resolve().parents[2] / "configs/colors_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("dataset_id") != "colors_v1":
        raise ValueError("invalid COLORS_V1 configuration")
    mapping = {variant: label["id"] for label in config["labels"] for variant in label["variants"]}
    templates, masks, labels, variants = [], [], [], []
    seen = set()
    for item in records:
        identifier = item.get("video_id", "")
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", identifier) or identifier in seen:
            raise ValueError("invalid or duplicate video_id")
        seen.add(identifier)
        variant = item.get("sign_variant_id")
        if not isinstance(variant, str) or variant not in mapping or mapping[variant] != item.get("semantic_label"):
            raise ValueError("semantic label and variant do not match configuration")
        if item.get("local_experimental_training_permission") not in ("owner_confirmed", "owner_confirmed_2026-11-01"):
            raise ValueError("local experimental use permission is not confirmed")
        review = item.get("linguistic_review_status")
        if review == "PENDING_REVIEW" and not allow_pending_review:
            raise ValueError("linguistic review is pending; experimental override required")
        if review not in ("APPROVED", "PENDING_REVIEW"):
            raise ValueError("rejected or unknown review status cannot be used")
        path = feature_dir / (identifier + ".npz")
        if path.is_symlink():
            raise ValueError("feature file must not be a symlink")
        with np.load(path, allow_pickle=False) as data:
            landmarks, mask = data["landmarks"].astype(np.float32), data["presence_mask"].astype(np.float32)
            metadata = json.loads(str(data["metadata"].item()))
        check_features(landmarks, mask)
        if (metadata.get("feature_version") != FEATURE_VERSION or metadata.get("video_id") != identifier
                or metadata.get("source_sha256") != item.get("file_hash")
                or metadata.get("semantic_label") != item.get("semantic_label")
                or metadata.get("sign_variant_id") != item.get("sign_variant_id")):
            raise ValueError("feature provenance does not match manifest")
        templates.append(landmarks)
        masks.append(mask)
        labels.append(item["semantic_label"])
        variants.append(item["sign_variant_id"])
    metadata = {"dataset": "colors_v1", "model_id": "colors_v1_template_experimental",
                "feature_version": FEATURE_VERSION, "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                "sample_count": len(records), "status": "EXPERIMENTAL_NOT_VALIDATED",
                "calibration": "UNAVAILABLE", "review_override": allow_pending_review}
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        np.savez_compressed(stream, templates=np.stack(templates), masks=np.stack(masks),
                            labels=np.asarray(labels), variants=np.asarray(variants), metadata=json.dumps(metadata))
    return metadata


def load(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as package:
        result = {key: package[key].copy() for key in ("templates", "masks", "labels", "variants")}
        result["metadata"] = json.loads(str(package["metadata"].item()))
    count = len(result["labels"])
    if (not count or result["templates"].shape != (count, 60, 75, 3)
            or result["masks"].shape != (count, 60, 75) or len(result["variants"]) != count
            or result["metadata"].get("feature_version") != FEATURE_VERSION):
        raise ValueError("invalid experimental template package")
    for seq, mask in zip(result["templates"], result["masks"], strict=True):
        check_features(seq, mask)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-pending-review", action="store_true")
    args = parser.parse_args()
    print(json.dumps(fit(args.manifest, args.feature_dir, args.output,
                         allow_pending_review=args.allow_pending_review), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
