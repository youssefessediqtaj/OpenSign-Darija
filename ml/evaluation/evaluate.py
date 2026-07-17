from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a saved model artifact.")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    metrics_path = args.artifact_dir / "metrics.json"
    if not metrics_path.exists():
        raise SystemExit(f"Metrics file missing: {metrics_path}")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
