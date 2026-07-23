from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.training.train_mosl_v1 import MODEL_DIR, validate_model_package


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the complete local MoSL V1 ONNX model package."
    )
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    args = parser.parse_args()
    report = validate_model_package(args.model_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
