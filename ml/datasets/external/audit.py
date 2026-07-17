from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from ml.datasets.manifest import sha256_file

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def audit_tree(root: Path) -> dict[str, object]:
    files = [path for path in root.rglob("*") if path.is_file()]
    checksums: dict[str, list[str]] = defaultdict(list)
    extensions: Counter[str] = Counter()
    total_size = 0
    for path in files:
        extensions[path.suffix.lower() or "<none>"] += 1
        total_size += path.stat().st_size
        digest = sha256_file(path)
        checksums[digest].append(path.relative_to(root).as_posix())
    duplicates = {digest: paths for digest, paths in checksums.items() if len(paths) > 1}
    labels = Counter(path.parent.name for path in files)
    return {
        "root": root.as_posix(),
        "file_count": len(files),
        "total_size_bytes": total_size,
        "extensions": dict(sorted(extensions.items())),
        "image_count": sum(count for ext, count in extensions.items() if ext in IMAGE_EXTENSIONS),
        "video_count": sum(count for ext, count in extensions.items() if ext in VIDEO_EXTENSIONS),
        "duplicate_checksum_count": len(duplicates),
        "duplicates": duplicates,
        "labels_by_parent_directory": dict(labels.most_common()),
        "limitations": [
            "No class, signer, FPS, duration, or image validity claim is made without deeper inspectors.",
        ],
    }


def write_reports(report: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "external-dataset-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# External Dataset Audit",
        "",
        f"- Root: `{report['root']}`",
        f"- Files: {report['file_count']}",
        f"- Size bytes: {report['total_size_bytes']}",
        f"- Images: {report['image_count']}",
        f"- Videos: {report['video_count']}",
        f"- Duplicate checksums: {report['duplicate_checksum_count']}",
        "",
        "This report is structural only; it does not validate legal rights or label quality.",
    ]
    (output_dir / "external-dataset-audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="data/raw/external")
    parser.add_argument("--output", default="data/reports")
    args = parser.parse_args()
    report = audit_tree(Path(args.root))
    write_reports(report, Path(args.output))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
