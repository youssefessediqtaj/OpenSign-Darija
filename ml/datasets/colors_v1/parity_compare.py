"""Compare Python-normalized detector output with the browser-normalized saved tensor."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from ml.datasets.colors_v1.preprocess import sample_indices
from ml.preprocessing.landmark_schema_v1 import normalize_frame


def compare(directory: Path) -> dict[str, object]:
    raw = json.loads((directory / "python.json").read_text(encoding="utf-8"))
    browser = json.loads((directory / "browser-tensor.json").read_text(encoding="utf-8"))

    def group(values: list[list[float]], count: int) -> np.ndarray:
        points = np.full((count, 3), np.nan, dtype=np.float32)
        if values:
            points[:len(values)] = values
        return points

    frames = []
    for frame in raw:
        if len(frame["pose"]) > 12 and (frame["leftHand"] or frame["rightHand"]):
            frames.append(normalize_frame(group(frame["pose"], 33), group(frame["leftHand"], 21),
                                          group(frame["rightHand"], 21)))
    indices = sample_indices(len(frames))
    values = np.round(np.stack([frames[i].landmarks for i in indices]), 6)
    masks = np.stack([frames[i].presence_mask for i in indices])
    other = np.asarray([frame["landmarks"] for frame in browser["tensor"]])
    other_mask = np.asarray([frame["presence_mask"] for frame in browser["tensor"]])
    if values.shape != other.shape or masks.shape != other_mask.shape:
        raise ValueError("sequence shapes differ")
    diff = np.abs(values - other)
    return {"python_valid_frames": len(frames), "browser_valid_frames": browser["valid_count"],
            "mask_mismatches": int(np.count_nonzero(masks != other_mask)), "tensor_values": int(diff.size),
            "mean_abs_difference": float(np.mean(diff)), "p95_abs_difference": float(np.percentile(diff, 95)),
            "max_abs_difference": float(np.max(diff))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.directory)
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
