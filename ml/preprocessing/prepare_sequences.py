from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def prepare_sequences(manifest: dict[str, Any]) -> dict[str, Any]:
    items = manifest.get("items", [])
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    sequences = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sequences.append(
            {
                "recording_id": item.get("recording_id"),
                "sign_code": item.get("sign_code"),
                "split": item.get("split"),
                "feature_schema_version": item.get("feature_schema_version"),
                "landmark_object_key": item.get("landmark_object_key"),
                "checksum_landmarks": item.get("checksum_landmarks"),
            }
        )
    return {
        "dataset_name": manifest.get("dataset_name"),
        "version": manifest.get("version"),
        "sequence_count": len(sequences),
        "sequences": sequences,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a landmark sequence index.")
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/datasets/sequences.json"))
    args = parser.parse_args()

    sequence_index = prepare_sequences(json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(sequence_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "sequences": sequence_index["sequence_count"]}))


if __name__ == "__main__":
    main()
