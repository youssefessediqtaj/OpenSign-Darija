from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.datasets.mosl_video.manifest import (
    build_records,
    manifest_checksum,
    write_outputs,
)


ORIGINAL_DATASET_PREFIX = "-".join(("vedios", "dataset"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan the local MoSL video dataset.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/raw"),
        help="Dataset root containing the five mosl_videos_dataset_* folders.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/data/external/mosl-video-dataset/manifests"),
    )
    parser.add_argument("--current-prefix", default="raw")
    parser.add_argument("--original-prefix", default=ORIGINAL_DATASET_PREFIX)
    args = parser.parse_args()

    records = build_records(
        args.root,
        current_prefix=args.current_prefix,
        original_prefix=args.original_prefix,
    )
    summary = write_outputs(records, args.output)
    summary["manifest_sha256"] = manifest_checksum(args.output / "videos.jsonl")
    (args.output / "dataset-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
