from __future__ import annotations

import re
from pathlib import Path


SIGNER_PATTERNS = [re.compile(r"(?:signer|participant|person|s)[_-]?(\d+)", re.IGNORECASE)]


def resolve_signer(path: Path) -> tuple[str | None, str]:
    text = path.as_posix()
    for pattern in SIGNER_PATTERNS:
        match = pattern.search(text)
        if match:
            return f"external_signer_{int(match.group(1)):04d}", "filename_pattern"
    return None, "UNCONFIRMED"
