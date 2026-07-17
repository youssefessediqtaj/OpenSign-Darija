from __future__ import annotations

from pathlib import Path


def label_from_path(path: Path, root: Path) -> tuple[str, str]:
    relative = path.relative_to(root)
    if len(relative.parts) > 1:
        return relative.parts[0], "parent_directory"
    return path.stem, "filename"
