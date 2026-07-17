from __future__ import annotations

import argparse
import csv
from pathlib import Path

from ml.datasets.manifest import sha256_file
from ml.datasets.mosl_words.label_normalizer import normalize_arabic_label
from ml.datasets.mosl_words.signer_resolver import resolve_signer
from ml.datasets.mosl_words.subtitle_parser import label_from_path
from ml.datasets.mosl_words.video_inspector import discover_videos, inspect_video


def build_manifest(root: Path, output: Path, source_id: str = "mendeley_mosl_v1") -> list[dict[str, object]]:
    rows = []
    for index, path in enumerate(discover_videos(root), start=1):
        label, label_source = label_from_path(path, root)
        signer_id, signer_source = resolve_signer(path.relative_to(root))
        info = inspect_video(path)
        rows.append(
            {
                "sample_id": f"{source_id}_{index:08d}",
                "source_id": source_id,
                "source_version": "1",
                "relative_path": path.relative_to(root).as_posix(),
                "original_arabic_label": label,
                "normalized_arabic_label": normalize_arabic_label(label),
                "canonical_concept_code": "",
                "review_status": "PENDING_REVIEW",
                "label_source": label_source,
                "signer_id": signer_id or "",
                "signer_source": signer_source,
                "fps": info.get("fps"),
                "duration_ms": info.get("duration_ms"),
                "width": info.get("width"),
                "height": info.get("height"),
                "checksum": sha256_file(path),
                "license": "CC-BY-4.0",
                "split": "",
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["sample_id"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/raw/external/mendeley-mosl-v1/extracted")
    parser.add_argument("--output", default="data/processed/words/manifest.csv")
    args = parser.parse_args()
    rows = build_manifest(Path(args.root), Path(args.output))
    print(f"word manifest rows: {len(rows)}")


if __name__ == "__main__":
    main()
