from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST_PATH = Path("artifacts/datasets/manifest.json")
TRAINING_ALLOWED_STATUSES = {"READY", "PUBLISHED"}
FORBIDDEN_EXPORT_KEYS = {"email", "user_id", "password", "access_token", "refresh_token"}


@dataclass(frozen=True)
class ManifestItem:
    contribution_id: str
    recording_id: str
    contributor_public_id: str
    sign_code: str
    split: str
    landmark_object_key: str
    checksum_landmarks: str
    feature_schema_version: str
    status: str = "APPROVED"
    revoked: bool = False
    consent_model_training: bool = True
    license: str = "OPEN_DATASET_INTERNAL"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest introuvable: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Le manifest doit etre un objet JSON.")
    return payload


def manifest_items(manifest: dict[str, Any]) -> list[ManifestItem]:
    raw_items = manifest.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("manifest.items doit etre une liste.")
    items: list[ManifestItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ValueError("Chaque item du manifest doit etre un objet.")
        items.append(
            ManifestItem(
                contribution_id=str(raw.get("contribution_id", "")),
                recording_id=str(raw.get("recording_id", "")),
                contributor_public_id=str(raw.get("contributor_public_id", "")),
                sign_code=str(raw.get("sign_code", "")),
                split=str(raw.get("split", "")).upper(),
                landmark_object_key=str(raw.get("landmark_object_key", "")),
                checksum_landmarks=str(raw.get("checksum_landmarks", "")),
                feature_schema_version=str(raw.get("feature_schema_version", "")),
                status=str(raw.get("status", "APPROVED")),
                revoked=bool(raw.get("revoked", False)),
                consent_model_training=bool(raw.get("consent_model_training", True)),
                license=str(raw.get("license", "OPEN_DATASET_INTERNAL")),
            )
        )
    return items


def find_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_EXPORT_KEYS:
                findings.append(child_path)
            findings.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_forbidden_keys(child, f"{path}[{index}]"))
    return findings
