from __future__ import annotations

import os
import stat
import zipfile
from pathlib import Path

DEFAULT_MAX_FILES = int(os.getenv("EXTERNAL_DATA_MAX_FILES", "200000"))
DEFAULT_MAX_EXTRACTED_BYTES = int(os.getenv("EXTERNAL_DATA_MAX_EXTRACTED_BYTES", "50000000000"))


def is_safe_member(name: str) -> bool:
    path = Path(name)
    return not path.is_absolute() and ".." not in path.parts


def safe_extract_zip(
    archive: Path,
    output_dir: Path,
    max_files: int = DEFAULT_MAX_FILES,
    max_bytes: int = DEFAULT_MAX_EXTRACTED_BYTES,
) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    count = 0
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        if len(infos) > max_files:
            raise ValueError("archive contains too many files")
        for info in infos:
            if not is_safe_member(info.filename):
                raise ValueError(f"unsafe archive member: {info.filename}")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f"symbolic links are not allowed: {info.filename}")
            total += info.file_size
            if total > max_bytes:
                raise ValueError("archive exceeds extracted size limit")
        for info in infos:
            if info.is_dir():
                continue
            handle.extract(info, output_dir)
            count += 1
    return {"file_count": count, "total_size_bytes": total}
