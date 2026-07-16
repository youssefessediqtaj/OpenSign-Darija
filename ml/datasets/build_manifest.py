from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REDACTED_KEYS = {"email", "user_id", "password", "access_token", "refresh_token"}


def _contains_forbidden_identity_keys(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in REDACTED_KEYS or _contains_forbidden_identity_keys(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_identity_keys(child) for child in value)
    return False


def load_items(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("items", [])
    else:
        items = payload
    if not isinstance(items, list):
        raise ValueError("Input manifest must contain an items list.")
    if any(not isinstance(item, dict) for item in items):
        raise ValueError("Each manifest item must be an object.")
    if _contains_forbidden_identity_keys(items):
        raise ValueError("Manifest contains forbidden direct identity keys.")
    return items


def build_manifest(items: list[dict[str, Any]], dataset_name: str, version: str) -> dict[str, Any]:
    contributors = sorted({str(item.get("contributor_public_id", "")) for item in items})
    contributors = [contributor for contributor in contributors if contributor]
    return {
        "dataset_name": dataset_name,
        "version": version,
        "generated_at": datetime.now(UTC).isoformat(),
        "privacy": {
            "anonymous_contributor_ids_only": True,
            "contains_email": False,
            "contains_user_id": False,
            "contains_audio": False,
        },
        "counts": {
            "items": len(items),
            "contributors": len(contributors),
        },
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a dataset manifest JSON file.")
    parser.add_argument("--input", type=Path, default=None, help="Optional raw approved-items JSON.")
    parser.add_argument("--output", type=Path, default=Path("artifacts/datasets/manifest.json"))
    parser.add_argument("--dataset-name", default="opensign-darija-pilot")
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()

    manifest = build_manifest(load_items(args.input), args.dataset_name, args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "items": manifest["counts"]["items"]}, indent=2))


if __name__ == "__main__":
    main()
