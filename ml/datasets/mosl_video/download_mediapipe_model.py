from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from ml.datasets.mosl_video.preprocess import (
    DEFAULT_MEDIAPIPE_MODEL_PATH,
    DEFAULT_MEDIAPIPE_MODEL_URL,
    download_mediapipe_model,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the MediaPipe Holistic task model."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            Path(os.environ["MEDIAPIPE_HOLISTIC_MODEL_PATH"])
            if os.environ.get("MEDIAPIPE_HOLISTIC_MODEL_PATH")
            else DEFAULT_MEDIAPIPE_MODEL_PATH
        ),
    )
    parser.add_argument(
        "--url",
        default=os.environ.get(
            "MEDIAPIPE_HOLISTIC_MODEL_URL", DEFAULT_MEDIAPIPE_MODEL_URL
        ),
    )
    args = parser.parse_args()

    path = (
        args.output
        if args.output.exists()
        else download_mediapipe_model(args.output, args.url)
    )
    result = {
        "path": path.as_posix(),
        "url": args.url,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
