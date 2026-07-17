from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a PyTorch checkpoint to ONNX.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()
    if not args.checkpoint.exists():
        raise SystemExit(f"Checkpoint missing: {args.checkpoint}")
    try:
        import torch  # noqa: F401
    except ModuleNotFoundError as exc:
        raise SystemExit("PyTorch is required for ONNX export.") from exc
    raise SystemExit(
        "ONNX export requires a validated trained GRU checkpoint; none is produced by the current empty dataset."
    )


if __name__ == "__main__":
    main()
