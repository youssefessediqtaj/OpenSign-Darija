from __future__ import annotations

from collections import defaultdict

from ml.datasets.manifest import ManifestItem


ALLOWED_SPLITS = {"TRAIN", "VALIDATION", "TEST", "HOLDOUT"}


def split_report(items: list[ManifestItem]) -> dict[str, object]:
    contributors_by_split: dict[str, set[str]] = defaultdict(set)
    classes_by_split: dict[str, set[str]] = defaultdict(set)
    sequences_by_split: dict[str, int] = defaultdict(int)
    for item in items:
        contributors_by_split[item.split].add(item.contributor_public_id)
        classes_by_split[item.split].add(item.sign_code)
        sequences_by_split[item.split] += 1

    leaks: list[dict[str, object]] = []
    split_names = sorted(contributors_by_split)
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            overlap = contributors_by_split[left].intersection(contributors_by_split[right])
            if overlap:
                leaks.append({"splits": [left, right], "contributors": sorted(overlap)})

    return {
        "contributors_by_split": {
            split: sorted(contributors) for split, contributors in contributors_by_split.items()
        },
        "classes_by_split": {
            split: sorted(classes) for split, classes in classes_by_split.items()
        },
        "sequences_by_split": dict(sorted(sequences_by_split.items())),
        "leaks": leaks,
    }


def validate_signer_independent_splits(items: list[ManifestItem]) -> list[str]:
    errors: list[str] = []
    for item in items:
        if item.split not in ALLOWED_SPLITS:
            errors.append(f"Split invalide pour {item.recording_id}: {item.split}")
    report = split_report(items)
    for leak in report["leaks"]:
        errors.append(
            "Contributeur present dans plusieurs splits: "
            f"{leak['splits']} -> {leak['contributors']}"
        )
    return errors
