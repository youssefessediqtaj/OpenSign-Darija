from __future__ import annotations

import os

DEFAULT_ALLOWED_LICENSES = {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0", "ODC-BY-1.0"}


def allowed_licenses() -> set[str]:
    raw = os.getenv("EXTERNAL_DATA_ALLOWED_LICENSES")
    if not raw:
        return DEFAULT_ALLOWED_LICENSES
    return {item.strip() for item in raw.split(",") if item.strip()}


def normalize_license(value: str | None) -> str:
    normalized = (value or "").strip().replace(" ", "-").upper()
    aliases = {
        "CC-BY-4.0": "CC-BY-4.0",
        "CC-BY-4": "CC-BY-4.0",
        "CC0": "CC0-1.0",
        "CC0-1.0": "CC0-1.0",
        "CC-BY-SA-4.0": "CC-BY-SA-4.0",
        "ODC-BY-1.0": "ODC-BY-1.0",
    }
    return aliases.get(normalized, value or "UNCONFIRMED")


def is_allowed_license(value: str | None) -> bool:
    return normalize_license(value) in allowed_licenses()
