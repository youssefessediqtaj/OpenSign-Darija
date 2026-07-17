from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.models.registry import validate_artifact_dir, write_checksums


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and stage a model artifact for registration.")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    report = validate_artifact_dir(args.artifact_dir)
    if report["valid"]:
        write_checksums(args.artifact_dir)
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
