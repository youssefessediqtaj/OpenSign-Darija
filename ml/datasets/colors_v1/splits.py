"""Deterministic grouped splitting for explicitly reviewed COLORS_V1 records."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any


def grouped_split(records: list[dict[str, Any]], *, seed: int = 42) -> dict[str, Any]:
    """Assign connected signer/lineage groups without leakage, or fail if coverage is impossible.

    Run metadata/media validation first. Every sample requires a known signer and lineage;
    generated appearances must retain the original signer identity. The output is an
    experimental split, not proof that the identity claims or scientific sample size are valid.
    """
    if not records:
        raise ValueError("no records to split")
    ids = [r.get("video_id") for r in records]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("unique video IDs required")
    for item in records:
        if any(not isinstance(item.get(k), str) or not item[k].strip()
               for k in ("semantic_label", "lineage_group_id", "signer_id")):
            raise ValueError("known label, lineage and signer required for every sample")
        if item.get("linguistic_review_status") != "APPROVED":
            raise ValueError("all samples must be linguistically approved")
        if item.get("consent_status") not in ("approved", "not_applicable"):
            raise ValueError("all samples require usable consent status")
        if item.get("source_type") not in ("source_reference_video", "original_recording", "synthetic_character_replacement", "augmented_recording"):
            raise ValueError("source type must be known")
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        parent[find(left)] = find(right)

    seen: dict[tuple[str, str], int] = {}
    by_id = {r["video_id"]: i for i, r in enumerate(records)}
    for i, item in enumerate(records):
        for field in ("lineage_group_id", "signer_id"):
            key = (field, item[field])
            if key in seen:
                union(i, seen[key])
            else:
                seen[key] = i
        source = item.get("source_video_id")
        if source:
            if source not in by_id:
                raise ValueError("source video is missing")
            union(i, by_id[source])
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for i, item in enumerate(records):
        groups[find(i)].append(item)
    components = sorted(groups.values(), key=lambda g: min(r["video_id"] for r in g))
    labels = {r["semantic_label"] for r in records}
    for label in labels:
        if sum(any(r["semantic_label"] == label for r in group) for group in components) < 3:
            raise ValueError(f"fewer than three independent groups for {label}")
    count = len(components)
    test_count = max(1, round(count * 0.2))
    val_count = max(1, round(count * 0.2))
    rng = random.Random(seed)
    for _ in range(2000):
        order = list(range(count))
        rng.shuffle(order)
        selections = {"test": order[:test_count], "validation": order[test_count:test_count + val_count],
                      "train": order[test_count + val_count:]}
        if all({r["semantic_label"] for i in indexes for r in components[i]} == labels
               for indexes in selections.values()):
            assignment = {r["video_id"]: split for split, indexes in selections.items()
                          for i in indexes for r in components[i]}
            return {"dataset": "colors_v1", "seed": seed, "group_count": count,
                    "assignments": assignment, "signer_disjoint_by_supplied_metadata": True,
                    "limitations": ["Supplied identities and linguistic reviews have not been independently verified.",
                                    "Small samples do not establish real-world generalization."]}
    raise ValueError("could not find a grouped split with every class in every partition")
