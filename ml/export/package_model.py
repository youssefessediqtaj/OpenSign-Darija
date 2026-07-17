from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ml.models.registry import validate_artifact_dir, write_checksums


def main() -> None:
    parser = argparse.ArgumentParser(description="Package a validated model artifact directory.")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_artifact_dir(args.artifact_dir)
    if not report["valid"]:
        raise SystemExit(f"Artifact invalid: {report}")
    write_checksums(args.artifact_dir)
    shutil.make_archive(str(args.output.with_suffix("")), "zip", args.artifact_dir)
    print(args.output.with_suffix(".zip"))


if __name__ == "__main__":
    main()
