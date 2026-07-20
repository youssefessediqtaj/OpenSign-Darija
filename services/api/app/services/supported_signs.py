from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import NoReturn, cast

from app.core.config import get_settings
from app.core.errors import ApiError

SUPPORTED_SIGNS_SCHEMA = "OPEN_SIGNE_SUPPORTED_SIGNS_V1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _unavailable() -> NoReturn:
    raise ApiError(
        "SUPPORTED_SIGNS_UNAVAILABLE",
        "Le vocabulaire du modèle actif est indisponible.",
        503,
    )


def _invalid(message: str = "Le vocabulaire du modèle est incompatible.") -> NoReturn:
    raise ApiError("SUPPORTED_SIGNS_INVALID", message, 503)


def _read_json(path: Path) -> object:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        _unavailable()
    except json.JSONDecodeError:
        _invalid()
    return payload


def _catalog_path() -> Path:
    configured = get_settings().supported_signs_path
    if not configured:
        _unavailable()
    path = Path(configured)
    if not path.is_file():
        _unavailable()
    return path


def _verified_package_files(catalog_path: Path) -> tuple[Path, Path, dict[str, object]]:
    labels_path = catalog_path.parent / "labels.json"
    checksums_path = catalog_path.parent / "checksums.json"
    if not labels_path.is_file() or not checksums_path.is_file():
        _unavailable()
    manifest_data = _read_json(checksums_path)
    if not isinstance(manifest_data, dict):
        _invalid("Le manifeste d’intégrité du modèle est invalide.")
    manifest = cast(dict[str, object], manifest_data)
    for filename, path in (
        ("supported-signs.json", catalog_path),
        ("labels.json", labels_path),
    ):
        expected_digest = manifest.get(filename)
        if not isinstance(expected_digest, str) or not SHA256_PATTERN.fullmatch(expected_digest):
            _invalid("Le manifeste d’intégrité du modèle est invalide.")
        try:
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            _unavailable()
        if actual_digest != expected_digest:
            _invalid("L’intégrité du vocabulaire du modèle n’est pas vérifiée.")
    return catalog_path, labels_path, manifest


def _load_package_catalog(path: Path) -> dict[str, str]:
    catalog_path, labels_path, _ = _verified_package_files(path)
    labels_data = _read_json(labels_path)
    if (
        not isinstance(labels_data, list)
        or not labels_data
        or any(not isinstance(label, str) or not label.strip() for label in labels_data)
    ):
        _invalid("La liste des classes du modèle est invalide.")
    labels = cast(list[str], labels_data)
    if len(labels) != len(set(labels)):
        _invalid("La liste des classes du modèle contient des doublons.")

    payload_data = _read_json(catalog_path)
    if not isinstance(payload_data, dict):
        _invalid()
    payload = cast(dict[str, object], payload_data)
    if payload.get("schema_version") != SUPPORTED_SIGNS_SCHEMA:
        _invalid()
    model_name = payload.get("model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        _invalid("Le nom du modèle est absent du vocabulaire.")
    signs_data = payload.get("signs")
    if not isinstance(signs_data, list):
        _invalid("Le vocabulaire du modèle est invalide.")

    catalog: dict[str, str] = {}
    for item_data in signs_data:
        if not isinstance(item_data, dict):
            _invalid("Une entrée du vocabulaire du modèle est invalide.")
        item = cast(dict[str, object], item_data)
        if item.get("status") != "SUPPORTED_FOR_TRAINING":
            continue
        key = item.get("label_key")
        label_ar = item.get("label_ar")
        if not isinstance(key, str) or not key.strip():
            _invalid("Une clé du vocabulaire du modèle est invalide.")
        if not isinstance(label_ar, str) or not label_ar.strip():
            _invalid("Un libellé arabe du vocabulaire du modèle est invalide.")
        if key in catalog:
            _invalid("Le vocabulaire du modèle contient des clés dupliquées.")
        catalog[key] = label_ar

    declared_size = payload.get("vocabulary_size")
    if type(declared_size) is not int or declared_size != len(catalog):
        _invalid("Le vocabulaire du modèle ne correspond pas aux classes déclarées.")
    if set(labels) != set(catalog):
        _invalid("Le vocabulaire arabe ne correspond pas aux classes du modèle.")
    return catalog


def supported_signs() -> dict[str, str]:
    return _load_package_catalog(_catalog_path())


def resolve_supported_sign(label_key: str) -> str:
    label_ar = supported_signs().get(label_key)
    if label_ar is None:
        raise ApiError("UNSUPPORTED_SIGN", "Ce signe n'est pas pris en charge.", 404)
    return label_ar
