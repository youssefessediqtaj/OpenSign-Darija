"""Generate a private, non-authoritative sign-interval review packet."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np

from ml.datasets.colors_v1.validate import _contained_file, sha256

STATUSES = {"PENDING", "APPROVED", "REJECTED", "NEEDS_CORRECTION"}


def validate_review(item: dict[str, Any], source: dict[str, Any]) -> None:
    """Validate a review entry without granting linguistic approval automatically."""
    if item.get("video_id") != source.get("video_id") or item.get("source_sha256") != source.get("file_hash"):
        raise ValueError("review does not match the source video and hash")
    for field in ("technical_review_status", "linguistic_review_status"):
        if item.get(field) not in STATUSES:
            raise ValueError(f"invalid {field}")
    if item["technical_review_status"] == "APPROVED":
        start, end = item.get("sign_start_time"), item.get("sign_end_time")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not 0 <= start < end:
            raise ValueError("approved technical review needs valid start/end")
        if not item.get("technical_reviewer") or not item.get("technical_review_date"):
            raise ValueError("approved technical review needs reviewer and date")
        date.fromisoformat(item["technical_review_date"])
    if item["linguistic_review_status"] == "APPROVED":
        if not item.get("linguistic_reviewer") or not item.get("linguistic_review_date"):
            raise ValueError("linguistic approval needs qualified reviewer and date")
        date.fromisoformat(item["linguistic_review_date"])


def generate(manifest: Path, root: Path, feature_dir: Path, output: Path) -> int:
    """Write timestamped previews and draft metadata without altering source or prior reviews."""
    import cv2

    root = root.resolve()
    if output.exists():
        raise FileExistsError("review output already exists; never overwrite reviews")
    if output.resolve().is_relative_to(root):
        raise ValueError("review output must be outside the source directory")
    records = json.loads(manifest.read_text(encoding="utf-8"))
    output.mkdir(parents=True, mode=0o700)
    reviews, sections = [], []
    for item in records:
        if not isinstance(item.get("video_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]+", item["video_id"]):
            raise ValueError("video_id must be a safe identifier")
        source = _contained_file(root, item["file_path"])
        if sha256(source) != item["file_hash"]:
            raise ValueError("source checksum changed")
        with np.load(feature_dir / (item["video_id"] + ".npz"), allow_pickle=False) as data:
            meta = json.loads(str(data["metadata"].item()))
            times = data["sampled_source_times_seconds"]
        if meta.get("source_sha256") != item["file_hash"]:
            raise ValueError("feature/source checksum mismatch")
        cap = cv2.VideoCapture(str(source))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        duration = float(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps if fps > 0 else 0
        if duration <= 0:
            cap.release()
            raise ValueError("unable to determine approximate duration")
        first, last = float(meta["first_hand_seconds"]), float(meta["last_hand_seconds"])
        candidates = np.linspace(max(0.0, first - 0.8), min(duration, last + 0.8), 8)
        sheet = np.full((2 * 210, 4 * 280, 3), 255, dtype=np.uint8)
        for i, timestamp in enumerate(candidates):
            cap.set(cv2.CAP_PROP_POS_MSEC, float(timestamp * 1000))
            ok, frame = cap.read()
            if not ok:
                cap.release()
                raise RuntimeError("preview frame decode failed")
            h, w = frame.shape[:2]
            scale = min(270 / w, 180 / h)
            small = cv2.resize(frame, (int(w * scale), int(h * scale)))
            y, x = (i // 4) * 210, (i % 4) * 280
            sheet[y + 22:y + 22 + small.shape[0], x:x + small.shape[1]] = small
            cv2.putText(sheet, f"~{timestamp:.2f}s", (x + 4, y + 16), cv2.FONT_HERSHEY_SIMPLEX, .48, (0, 0, 0), 1)
        cap.release()
        image = output / (item["video_id"] + ".jpg")
        if not cv2.imwrite(str(image), sheet):
            raise RuntimeError("preview creation failed")
        os.chmod(image, 0o600)
        distinct = np.unique(times)
        review = {"video_id": item["video_id"], "source_sha256": item["file_hash"],
                  "sign_start_time": None, "sign_end_time": None,
                  "suggested_first_detected_hand": first, "suggested_last_detected_hand": last,
                  "approximate_duration_seconds": round(duration, 3),
                  "segmentation_method": "hand_presence_suggestion_unreviewed",
                  "technical_review_status": "PENDING", "linguistic_review_status": "PENDING",
                  "technical_reviewer": None, "technical_review_date": None,
                  "linguistic_reviewer": None, "linguistic_review_date": None,
                  "detector_frames": meta["detector_frames"], "valid_frames": meta["valid_frames"],
                  "largest_sampled_gap_seconds": float(np.max(np.diff(distinct))) if len(distinct) > 1 else None,
                  "notes": "Review full motion, repetitions, occlusion, start and end; detection is not a boundary."}
        reviews.append(review)
        video_url = quote(os.path.relpath(source, output))
        sections.append(f'<section><h2>{html.escape(item["video_id"])}</h2>'
                        f'<video controls preload="metadata" width="480" src="{video_url}"></video><br>'
                        f'<img width="800" src="{html.escape(image.name)}" alt="Timestamped frames">'
                        f'<p>First–last hand: {first:.2f}–{last:.2f}s; review remains pending.</p></section>')
    (output / "review-draft.json").write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
    (output / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>Private sign review</title>'
        '<h1>Private sign review — pending</h1><p>Preview timestamps are approximate; inspect the full video. '
        'Record decisions in review-draft.json; technical and qualified linguistic reviews are separate.</p>'
        + ''.join(sections), encoding="utf-8")
    os.chmod(output / "review-draft.json", 0o600)
    os.chmod(output / "index.html", 0o600)
    return len(reviews)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--video-root", type=Path, required=True)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(f"Prepared {generate(args.manifest, args.video_root, args.feature_dir, args.output_dir)} pending reviews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
