from __future__ import annotations

from pathlib import Path
from typing import Any


def load_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and line.endswith(":"):
            key = line[:-1]
            current = {}
            root[key] = current
            continue
        if current is None or ":" not in line:
            raise ValueError(f"Unsupported config line: {raw_line}")
        key, value = [part.strip() for part in line.split(":", 1)]
        if value.startswith('"') and value.endswith('"'):
            parsed: Any = value[1:-1]
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        else:
            try:
                parsed = int(value)
            except ValueError:
                try:
                    parsed = float(value)
                except ValueError:
                    parsed = value
        current[key] = parsed
    return root
