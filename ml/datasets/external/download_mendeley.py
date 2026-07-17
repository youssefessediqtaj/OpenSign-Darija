from __future__ import annotations

import argparse
import json
from pathlib import Path


def prepare_manual_download(dataset_id: str, version: str, output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    metadata = {
        "dataset_id": dataset_id,
        "version": version,
        "doi": f"10.17632/{dataset_id}.{version}",
        "license": "CC-BY-4.0",
        "status": "MANUAL_DOWNLOAD_REQUIRED",
        "source_url": f"https://data.mendeley.com/datasets/{dataset_id}/{version}",
        "next_step": (
            "Download the archive from Mendeley Data without bypassing site protections, "
            "then run python -m ml.datasets.external.import_local_archive."
        ),
    }
    (output / "source-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_manual_download(args.dataset_id, args.version, Path(args.output)), indent=2))


if __name__ == "__main__":
    main()
