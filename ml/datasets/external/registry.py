from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REGISTRY_PATH = Path("ml/datasets/sources/external_sources.yaml")


@dataclass(frozen=True)
class ExternalSource:
    id: str
    source_type: str
    task_type: str
    expected_modality: str
    license: str
    license_status: str
    enabled: bool


def _parse_scalar(value: str) -> object:
    value = value.strip()
    if value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"\d+", value):
        return int(value)
    return value


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    sources: list[dict[str, object]] = []
    docs: list[dict[str, object]] = []
    allowed: list[str] = []
    section = ""
    current: dict[str, object] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            section = raw_line.rstrip(":")
            current = None
            continue
        stripped = raw_line.strip()
        if stripped.startswith("- ") and raw_line.startswith("  - "):
            body = stripped[2:]
            if section == "allowed_licenses":
                allowed.append(str(_parse_scalar(body)))
                continue
            current = {}
            if section == "sources":
                sources.append(current)
            elif section == "documentation_sources":
                docs.append(current)
            if ":" in body:
                key, value = body.split(":", 1)
                current[key.strip()] = _parse_scalar(value)
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _parse_scalar(value)
    return {
        "allowed_licenses": allowed,
        "sources": sources,
        "documentation_sources": docs,
    }


def list_sources(path: Path = REGISTRY_PATH) -> list[ExternalSource]:
    payload = load_registry(path)
    sources = []
    for item in payload["sources"]:
        if not isinstance(item, dict):
            continue
        sources.append(
            ExternalSource(
                id=str(item.get("id", "")),
                source_type=str(item.get("source_type", "")),
                task_type=str(item.get("task_type", "")),
                expected_modality=str(item.get("expected_modality", "")),
                license=str(item.get("license", "UNCONFIRMED")),
                license_status=str(item.get("license_status", "UNKNOWN")),
                enabled=bool(item.get("enabled", False)),
            )
        )
    return sources


def get_source(source_id: str, path: Path = REGISTRY_PATH) -> ExternalSource:
    for source in list_sources(path):
        if source.id == source_id:
            return source
    raise KeyError(source_id)


def validate_no_duplicate_documentation_sources(path: Path = REGISTRY_PATH) -> None:
    payload = load_registry(path)
    source_ids = {str(item.get("id")) for item in payload["sources"] if isinstance(item, dict)}
    for doc in payload["documentation_sources"]:
        if not isinstance(doc, dict):
            continue
        doc_id = str(doc.get("id"))
        if doc_id in source_ids:
            raise ValueError(f"documentation source {doc_id} is also counted as a dataset")
        if doc.get("counted_as_dataset") is True:
            raise ValueError(f"documentation source {doc_id} must not be counted as a dataset")
