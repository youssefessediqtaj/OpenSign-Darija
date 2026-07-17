from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--feature-schema", default="1.0.0")
    parser.add_argument("--target-frames", type=int, default=30)
    args = parser.parse_args()
    output = Path("data/interim/words/landmarks")
    output.mkdir(parents=True, exist_ok=True)
    raise SystemExit(
        "MediaPipe batch extraction is scaffolded but not run without local videos; "
        f"source={args.source} schema={args.feature_schema} target_frames={args.target_frames}"
    )


if __name__ == "__main__":
    main()
