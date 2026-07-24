from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if path.is_file()
        and not any(
            part
            in {
                ".git",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                ".venv",
                "dist",
                "node_modules",
            }
            for part in path.parts
        )
    )


def local_markdown_targets(path: Path) -> list[tuple[int, str]]:
    targets: list[tuple[int, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for match in MARKDOWN_LINK.finditer(line):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if target.startswith(("/api/", "/health")):
                continue
            target = target.split("#", 1)[0].strip("<>")
            if target:
                targets.append((line_number, target))
    return targets


def test_repository_markdown_links_resolve() -> None:
    missing: list[str] = []
    for path in markdown_files():
        for line_number, target in local_markdown_targets(path):
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                missing.append(f"{path.relative_to(ROOT)}:{line_number} escapes repo: {target}")
                continue
            if not resolved.exists():
                missing.append(f"{path.relative_to(ROOT)}:{line_number} -> {target}")
    assert not missing, "\n".join(missing)
