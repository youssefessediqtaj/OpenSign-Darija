"""Register additional private videos without copying, mutating or approving them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.datasets.colors_v1.validate import validate, write_private_report


def extend(base: Path, additions: Path, config: Path, video_root: Path, output: Path) -> int:
    existing = json.loads(base.read_text(encoding="utf-8"))
    new = json.loads(additions.read_text(encoding="utf-8"))
    if not isinstance(existing, list) or not isinstance(new, list) or not new:
        raise ValueError("base and nonempty additions must be JSON arrays")
    for item in new:
        if not isinstance(item, dict):
            raise ValueError("each addition must be an object")
        if item.get("linguistic_review_status") != "PENDING_REVIEW":
            raise ValueError("new additions must begin with pending linguistic review")
        if item.get("source_type") in ("synthetic_character_replacement", "augmented_recording"):
            if not item.get("source_video_id") or not item.get("transformation_type"):
                raise ValueError("derived videos require parent and transformation metadata")
    combined = existing + new
    result = validate(json.loads(config.read_text(encoding="utf-8")), combined, video_root)
    if result["errors"]:
        raise ValueError("manifest validation failed: " + "; ".join(result["errors"]))
    # Preserve declared data exactly; computed hashes and media properties are in the separate validation report.
    write_private_report(output, json.dumps(combined, ensure_ascii=False, indent=2) + "\n", video_root)
    return len(new)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--additions", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("ml/configs/colors_v1.json"))
    parser.add_argument("--video-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        count = extend(args.base, args.additions, args.config, args.video_root, args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Registration failed: {exc}\n")
    print(f"Registered {count} additions with pending linguistic review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
