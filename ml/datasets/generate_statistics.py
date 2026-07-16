from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def generate_statistics(manifest: dict[str, Any]) -> dict[str, Any]:
    items = manifest.get("items", [])
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    splits = Counter(str(item.get("split", "unknown")) for item in items if isinstance(item, dict))
    signs = Counter(str(item.get("sign_code", "unknown")) for item in items if isinstance(item, dict))
    contributors = {
        str(item.get("contributor_public_id"))
        for item in items
        if isinstance(item, dict) and item.get("contributor_public_id")
    }
    videos = sum(1 for item in items if isinstance(item, dict) and item.get("video_object_key"))
    return {
        "dataset_name": manifest.get("dataset_name"),
        "version": manifest.get("version"),
        "total_items": len(items),
        "contributors": len(contributors),
        "splits": dict(sorted(splits.items())),
        "signs": dict(sorted(signs.items())),
        "video_items": videos,
        "landmark_only_items": len(items) - videos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dataset statistics from a manifest.")
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/datasets/statistics.json"))
    args = parser.parse_args()

    stats = generate_statistics(json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
