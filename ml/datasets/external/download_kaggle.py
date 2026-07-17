from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from ml.datasets.external.licenses import is_allowed_license, normalize_license


def has_kaggle_credentials() -> bool:
    config = Path.home() / ".kaggle" / "kaggle.json"
    return bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")) or config.exists()


def run_kaggle_metadata(dataset: str, output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    command = ["kaggle", "datasets", "metadata", dataset, "-p", str(output)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    metadata_path = output / "dataset-metadata.json"
    if not metadata_path.exists():
        raise RuntimeError(f"Kaggle metadata missing after CLI call: {completed.stdout[:200]}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def download(dataset: str, output: Path, yes: bool = False) -> dict[str, object]:
    if not has_kaggle_credentials():
        raise SystemExit("Kaggle credentials not found; set KAGGLE_USERNAME/KAGGLE_KEY or ~/.kaggle/kaggle.json")
    metadata = run_kaggle_metadata(dataset, output)
    license_name = normalize_license(str(metadata.get("licenses", [{}])[0].get("name", "")))
    if not is_allowed_license(license_name):
        report = {
            "dataset": dataset,
            "license": license_name,
            "status": "LICENSE_BLOCKED",
            "training_enabled": False,
        }
        (output / "import-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise SystemExit(f"Kaggle license is not verified/allowed: {license_name}")
    if not yes:
        raise SystemExit("Re-run with --yes after reviewing Kaggle metadata and license")
    command = ["kaggle", "datasets", "download", dataset, "-p", str(output)]
    subprocess.run(command, check=True)
    return {"dataset": dataset, "license": license_name, "status": "DOWNLOADED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    print(json.dumps(download(args.dataset, Path(args.output), args.yes), indent=2))


if __name__ == "__main__":
    main()
