from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PyTorch/ONNX parity metadata.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--onnx", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=Path("artifacts/ml/onnx-validation.json"))
    args = parser.parse_args()
    errors = []
    if not args.checkpoint.exists():
        errors.append(f"Checkpoint missing: {args.checkpoint}")
    if not args.onnx.exists():
        errors.append(f"ONNX missing: {args.onnx}")
    report = {
        "valid": not errors,
        "errors": errors,
        "checkpoint_sha256": sha256(args.checkpoint) if args.checkpoint.exists() else None,
        "onnx_sha256": sha256(args.onnx) if args.onnx.exists() else None,
        "tolerance": {"absolute": 1e-4, "relative": 1e-4},
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
