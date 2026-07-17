from __future__ import annotations

import json

from ml.datasets.external.licenses import is_allowed_license
from ml.datasets.external.registry import list_sources, validate_no_duplicate_documentation_sources


def validate() -> dict[str, object]:
    validate_no_duplicate_documentation_sources()
    sources = list_sources()
    results = []
    valid = True
    for source in sources:
        allowed = source.license_status == "VERIFIED" and is_allowed_license(source.license)
        if source.enabled and not allowed:
            valid = False
        results.append(
            {
                "id": source.id,
                "enabled": source.enabled,
                "license": source.license,
                "license_status": source.license_status,
                "allowed_for_training": allowed,
            }
        )
    return {"valid": valid, "sources": results}


def main() -> None:
    report = validate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
