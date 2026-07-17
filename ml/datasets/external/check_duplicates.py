from __future__ import annotations

import json
from pathlib import Path

from ml.datasets.external.audit import audit_tree
from ml.datasets.external.registry import validate_no_duplicate_documentation_sources


def main() -> None:
    validate_no_duplicate_documentation_sources()
    roots = [path for path in Path("data/raw/external").glob("*") if path.is_dir()]
    checksum_to_source: dict[str, list[str]] = {}
    for root in roots:
        report = audit_tree(root)
        for digest, paths in dict(report.get("duplicates", {})).items():
            checksum_to_source.setdefault(str(digest), []).extend(
                f"{root.name}:{path}" for path in paths
            )
    cross_source = {
        digest: paths
        for digest, paths in checksum_to_source.items()
        if len({path.split(":", 1)[0] for path in paths}) > 1
    }
    result = {"valid": not cross_source, "cross_source_duplicates": cross_source}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if cross_source:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
