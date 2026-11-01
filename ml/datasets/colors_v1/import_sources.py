"""Safely import the owner-supplied source archive into a new private directory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

FILES = {
    "black(1).mov": ("black", "black_variant_01"),
    "Bleu.mov": ("blue", "blue_variant_01"),
    "Bleu-2.mov": ("blue", "blue_variant_02"),
    "Brown.mov": ("brown", "brown_variant_01"),
    "Green.mov": ("green", "green_variant_01"),
    "Orange.mov": ("orange", "orange_variant_01"),
    "Pink.mov": ("pink", "pink_variant_01"),
    "Red.mov": ("red", "red_variant_01"),
    "White.mov": ("white", "white_variant_01"),
    "yellow.mov": ("yellow", "yellow_variant_01"),
}


def import_archive(archive: Path, destination: Path, *, local_training_permitted: bool = False) -> dict[str, object]:
    """Copy only the expected files after strict path, mapping and digest checks."""
    if destination.exists():
        raise FileExistsError("destination already exists; refusing to overwrite")
    expected = {"README.txt", "source_manifest.csv", "SHA256SUMS.txt"} | {
        f"videos/{name}" for name in FILES
    }
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("archive members differ from the exact expected file list")
        for entry in infos:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in entry.filename:
                raise ValueError("unsafe archive path")
            if stat.S_ISLNK(entry.external_attr >> 16) or entry.is_dir():
                raise ValueError("symlinks and directory members are not accepted")
            if entry.file_size > 200_000_000:
                raise ValueError("archive member too large")
        rows = list(csv.DictReader(io.StringIO(zipped.read("source_manifest.csv").decode("utf-8-sig"))))
        if len(rows) != len(FILES):
            raise ValueError("source manifest must contain ten records")
        source_map = {row["file_path"]: row for row in rows}
        if len(source_map) != len(FILES):
            raise ValueError("source manifest contains duplicates")
        for name, (label, variant) in FILES.items():
            row = source_map.get(f"videos/{name}")
            if not row or row.get("semantic_label") != label or row.get("sign_variant_id") != variant:
                raise ValueError("source mapping does not match the confirmed vocabulary")
        checksums = {}
        for line in zipped.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, name = line.split("  ", 1)
            if name in checksums or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("invalid checksum list")
            checksums[name] = digest
        if set(checksums) != {f"videos/{name}" for name in FILES}:
            raise ValueError("checksum list does not match source videos")
        with tempfile.TemporaryDirectory(prefix=".colors-import-", dir=destination.parent) as temporary:
            staging = Path(temporary) / "dataset"
            staging.mkdir(mode=0o700)
            (staging / "videos").mkdir(mode=0o700)
            records = []
            for name, (label, variant) in FILES.items():
                key = f"videos/{name}"
                target = staging / key
                digest = hashlib.sha256()
                with zipped.open(key) as source, target.open("xb") as output:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(chunk)
                        output.write(chunk)
                os.chmod(target, 0o600)
                if digest.hexdigest() != checksums[key]:
                    raise ValueError(f"checksum mismatch: {key}")
                row = source_map[key]
                records.append({
                    "video_id": variant, "semantic_label": label, "sign_variant_id": variant,
                    "file_path": key, "file_hash": digest.hexdigest(),
                    "source_type": "source_reference_video", "source_video_id": None,
                    "lineage_group_id": row.get("lineage_group_id") or variant,
                    "signer_id": None, "performer_profile": None,
                    "license": "UNCONFIRMED", "consent_status": "pending",
                    "provenance": "User-supplied source package; original provenance unconfirmed",
                    "linguistic_review_status": "PENDING_REVIEW", "split": "unassigned",
                    "local_experimental_training_permission": "owner_confirmed" if local_training_permitted else "UNCONFIRMED",
                })
            for name in ("README.txt", "source_manifest.csv", "SHA256SUMS.txt"):
                target = staging / name
                target.write_bytes(zipped.read(name))
                os.chmod(target, 0o600)
            manifest = staging / "manifest.json"
            manifest.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.chmod(manifest, 0o600)
            os.rename(staging, destination)
    return {"imported": len(records), "dataset_id": "colors_v1", "destination": str(destination)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--local-training-permitted", action="store_true", help="only when the owner has confirmed this permission")
    args = parser.parse_args()
    try:
        print(json.dumps(import_archive(args.archive, args.destination, local_training_permitted=args.local_training_permitted), indent=2))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"Import failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
