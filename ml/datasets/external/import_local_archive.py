from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ml.datasets.external.licenses import is_allowed_license
from ml.datasets.external.registry import get_source
from ml.datasets.external.safe_archive import safe_extract_zip
from ml.datasets.manifest import sha256_file


def import_archive(source_id: str, archive: Path, output: Path) -> dict[str, object]:
    source = get_source(source_id)
    if source.license_status != "VERIFIED" or not is_allowed_license(source.license):
        raise SystemExit(f"Source {source_id} is not license-verified for import")
    if not archive.exists():
        raise FileNotFoundError(archive)
    output.mkdir(parents=True, exist_ok=True)
    archive_dir = output / "archives"
    extract_dir = output / "extracted"
    archive_dir.mkdir(exist_ok=True)
    preserved = archive_dir / archive.name
    if archive.resolve() != preserved.resolve():
        shutil.copy2(archive, preserved)
    checksum = sha256_file(preserved)
    extraction = safe_extract_zip(preserved, extract_dir)
    report = {
        "source_id": source_id,
        "archive": preserved.relative_to(output).as_posix(),
        "archive_checksum": checksum,
        "file_count": extraction["file_count"],
        "total_size_bytes": extraction["total_size_bytes"],
        "imported_at": datetime.now(UTC).isoformat(),
        "raw_immutable": True,
    }
    (output / "source-metadata.json").write_text(
        json.dumps({"source_id": source_id, "license": source.license}, indent=2),
        encoding="utf-8",
    )
    (output / "checksums.sha256").write_text(f"{checksum}  {preserved.name}\n", encoding="utf-8")
    (output / "import-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    output = Path(args.output) if args.output else Path("data/raw/external") / args.source
    print(json.dumps(import_archive(args.source, Path(args.archive), output), indent=2))


if __name__ == "__main__":
    main()
