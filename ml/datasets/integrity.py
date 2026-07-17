from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from ml.datasets.manifest import (
    DEFAULT_MANIFEST_PATH,
    TRAINING_ALLOWED_STATUSES,
    find_forbidden_keys,
    load_manifest,
    manifest_items,
    sha256_file,
)
from ml.datasets.split_validator import split_report, validate_signer_independent_splits


@dataclass(frozen=True)
class TrainingDatasetThresholds:
    min_contributors_per_sign: int = 8
    min_repetitions_per_sign: int = 80
    min_validation_contributors_per_sign: int = 2
    min_test_contributors_per_sign: int = 2


def _local_landmark_path(object_key: str, root: Path) -> Path:
    return root / object_key


def validate_training_dataset(
    *,
    dataset_version: str,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    feature_schema_version: str = "1.0.0",
    landmark_root: Path = Path("artifacts/landmarks"),
    thresholds: TrainingDatasetThresholds = TrainingDatasetThresholds(),
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, object] = {}

    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        return {
            "valid": False,
            "dataset_version": dataset_version,
            "errors": [str(exc)],
            "warnings": [],
            "statistics": {},
        }

    if str(manifest.get("version")) != dataset_version:
        errors.append(
            f"Version manifest incompatible: attendu {dataset_version}, recu {manifest.get('version')}"
        )
    status = str(manifest.get("status", "UNCONFIRMED"))
    if status not in TRAINING_ALLOWED_STATUSES:
        errors.append(f"Statut dataset non autorise pour entrainement: {status}")

    forbidden = find_forbidden_keys(manifest)
    if forbidden:
        errors.append(f"Champs identifiants interdits trouves: {', '.join(forbidden[:10])}")

    try:
        items = manifest_items(manifest)
    except Exception as exc:
        items = []
        errors.append(str(exc))

    if not items:
        errors.append("Aucun exemple disponible; entrainement refuse.")

    class_counts = Counter(item.sign_code for item in items)
    contributors_by_class: dict[str, set[str]] = defaultdict(set)
    validation_contributors_by_class: dict[str, set[str]] = defaultdict(set)
    test_contributors_by_class: dict[str, set[str]] = defaultdict(set)
    for item in items:
        contributors_by_class[item.sign_code].add(item.contributor_public_id)
        if item.split == "VALIDATION":
            validation_contributors_by_class[item.sign_code].add(item.contributor_public_id)
        if item.split == "TEST":
            test_contributors_by_class[item.sign_code].add(item.contributor_public_id)
        if item.status != "APPROVED":
            errors.append(f"Contribution non approuvee dans le manifest: {item.contribution_id}")
        if item.revoked:
            errors.append(f"Contribution revoquee incluse: {item.contribution_id}")
        if not item.consent_model_training:
            errors.append(f"Consentement MODEL_TRAINING absent: {item.contribution_id}")
        if item.feature_schema_version != feature_schema_version:
            errors.append(
                f"Schema incompatible pour {item.recording_id}: "
                f"{item.feature_schema_version} != {feature_schema_version}"
            )
        if item.license not in {"OPEN_DATASET_INTERNAL", "RESEARCH_CONSENTED"}:
            errors.append(f"Licence incompatible pour {item.recording_id}: {item.license}")
        local_path = _local_landmark_path(item.landmark_object_key, landmark_root)
        if local_path.exists():
            checksum = sha256_file(local_path)
            if item.checksum_landmarks and checksum != item.checksum_landmarks:
                errors.append(f"Checksum landmarks incorrect pour {item.recording_id}")
            try:
                payload = json.loads(local_path.read_text(encoding="utf-8"))
                frames = payload.get("frames", []) if isinstance(payload, dict) else []
                if not frames:
                    errors.append(f"Landmarks vides pour {item.recording_id}")
            except Exception as exc:
                errors.append(f"Landmarks illisibles pour {item.recording_id}: {exc}")
        else:
            errors.append(f"Fichier landmarks manquant: {item.landmark_object_key}")

    errors.extend(validate_signer_independent_splits(items))
    eligible_classes: list[str] = []
    excluded_classes: list[dict[str, object]] = []
    for sign_code, count in sorted(class_counts.items()):
        contributor_count = len(contributors_by_class[sign_code])
        validation_count = len(validation_contributors_by_class[sign_code])
        test_count = len(test_contributors_by_class[sign_code])
        reasons = []
        if contributor_count < thresholds.min_contributors_per_sign:
            reasons.append(
                f"{contributor_count} contributeurs < {thresholds.min_contributors_per_sign}"
            )
        if count < thresholds.min_repetitions_per_sign:
            reasons.append(f"{count} repetitions < {thresholds.min_repetitions_per_sign}")
        if validation_count < thresholds.min_validation_contributors_per_sign:
            reasons.append(
                f"{validation_count} contributeurs validation < "
                f"{thresholds.min_validation_contributors_per_sign}"
            )
        if test_count < thresholds.min_test_contributors_per_sign:
            reasons.append(
                f"{test_count} contributeurs test < {thresholds.min_test_contributors_per_sign}"
            )
        if reasons:
            excluded_classes.append({"sign_code": sign_code, "reasons": reasons})
        else:
            eligible_classes.append(sign_code)

    if excluded_classes:
        warnings.append("Certaines classes sont exclues du vocabulaire pilote.")
    if not eligible_classes:
        errors.append("Aucune classe ne respecte les seuils minimaux du vocabulaire pilote.")

    stats.update(
        {
            "items": len(items),
            "classes": len(class_counts),
            "contributors": len({item.contributor_public_id for item in items}),
            "class_counts": dict(sorted(class_counts.items())),
            "eligible_classes": eligible_classes,
            "excluded_classes": excluded_classes,
            "splits": split_report(items),
        }
    )
    return {
        "valid": not errors,
        "dataset_version": dataset_version,
        "manifest_path": str(manifest_path),
        "errors": errors,
        "warnings": warnings,
        "statistics": stats,
    }
