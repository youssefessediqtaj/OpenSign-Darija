import json
from pathlib import Path

import numpy as np

from ml.datasets.mosl_video.categories import CATEGORY_BY_FOLDER
from ml.datasets.mosl_video.label_parser import parse_mosl_label
from ml.datasets.mosl_video.manifest import discover_videos
from ml.datasets.mosl_video.training_manifest import prepare_training_manifest
from ml.datasets.mosl_video.validate_processed_artifacts import validate_manifest


def test_label_parser_extracts_trailing_sign_variant() -> None:
    parsed = parse_mosl_label("آسِفٌ (إِشَارَة 2).mp4")

    assert parsed.raw_label == "آسِفٌ (إِشَارَة 2)"
    assert parsed.normalized_label_ar == "آسِفٌ"
    assert parsed.label_key == "اسف"
    assert parsed.variant_index == 2


def test_label_parser_preserves_internal_parentheses() -> None:
    parsed = parse_mosl_label("فَرَاغٌ (وَقْت).mp4")

    assert parsed.normalized_label_ar == "فَرَاغٌ (وَقْت)"
    assert parsed.label_key == "فراغ_وقت"
    assert parsed.variant_index == 1


def test_letters_map_to_alphabet_static() -> None:
    assert CATEGORY_BY_FOLDER["mosl_videos_dataset_Letters"].mode == "ALPHABET_STATIC"


def test_non_letters_map_to_word_isolated() -> None:
    assert CATEGORY_BY_FOLDER["mosl_videos_dataset_Diverse"].mode == "WORD_ISOLATED"
    assert CATEGORY_BY_FOLDER["mosl_videos_dataset_Numbers"].mode == "WORD_ISOLATED"
    assert CATEGORY_BY_FOLDER["mosl_videos_dataset_Pronouns"].mode == "WORD_ISOLATED"
    assert (
        CATEGORY_BY_FOLDER["mosl_videos_dataset_days_months_seasons"].mode
        == "WORD_ISOLATED"
    )


def test_source_dataset_inventory_when_present() -> None:
    project_root = "".join(
        ("Multimodal-", "Moroccan-", "Sign-", "Language-", "Generation")
    )
    dataset_dir = "-".join(("vedios", "dataset"))
    root = Path(project_root) / dataset_dir
    if not root.exists():
        return

    videos = discover_videos(root)

    assert len(videos) == 2216
    assert any(path.name.endswith(".mp4") for path in videos)


def write_cache(path: Path, sha256: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        landmarks=np.zeros((60, 75, 3), dtype=np.float32),
        presence_mask=np.ones((60, 75), dtype=np.float32),
        metadata=np.array(
            json.dumps(
                {
                    "source_sha256": sha256,
                    "schema_version": "OPEN_SIGNE_LANDMARK_SCHEMA_V1",
                    "preprocessing_version": "mediapipe_tasks_holistic_v1",
                    "coordinate_format": "shoulder_centered_v1",
                    "frames": 4,
                    "landmarks_per_frame": 75,
                    "coordinates": 3,
                    "label_key": "a",
                    "mode": "WORD_ISOLATED",
                }
            )
        ),
    )


def test_training_manifest_adapter_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "videos.jsonl"
    splits = tmp_path / "splits"
    processed = tmp_path / "processed"
    output = tmp_path / "manifest.json"
    report_json = tmp_path / "eligibility.json"
    report_csv = tmp_path / "eligibility.csv"
    records = []
    for label in ("b", "a"):
        for index, split in enumerate(("train", "validation", "test")):
            sha = f"{label}{index}".ljust(64, "0")
            records.append(
                {
                    "sha256": sha,
                    "mode": "WORD_ISOLATED",
                    "label_key": label,
                    "normalized_label_ar": label,
                    "current_relative_path": f"raw/{sha}.mp4",
                }
            )
            write_cache(processed / f"{sha}.npz", sha)
            split_path = splits / f"word-isolated-{split}.json"
            split_path.parent.mkdir(parents=True, exist_ok=True)
            existing = json.loads(split_path.read_text()) if split_path.exists() else []
            existing.append({"sha256": sha})
            split_path.write_text(json.dumps(existing), encoding="utf-8")
    source.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )

    first = prepare_training_manifest(
        source, splits, processed, output, report_json, report_csv
    )
    second = prepare_training_manifest(
        source, splits, processed, output, report_json, report_csv
    )

    assert first["label_index"] == {"a": 0, "b": 1}
    assert second["label_index"] == first["label_index"]
    assert len(first["eligible_samples"]) == 6
    assert all(sample["dataset_manifest_checksum"] for sample in first["samples"])
    assert {sample["split"] for sample in first["samples"]} == {
        "train",
        "validation",
        "test",
    }
    assert report_json.exists()
    assert report_csv.exists()


def test_processed_artifact_validation_reports_valid_cache(tmp_path: Path) -> None:
    sha = "a0".ljust(64, "0")
    manifest = tmp_path / "videos.jsonl"
    processed = tmp_path / "processed"
    output = tmp_path / "validation.json"
    write_cache(processed / f"{sha}.npz", sha)
    manifest.write_text(
        json.dumps(
            {
                "sha256": sha,
                "mode": "WORD_ISOLATED",
                "label_key": "a",
                "current_relative_path": "raw/a.mp4",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_manifest(manifest, processed, output)

    assert report["valid"] is True
    assert report["valid_artifacts"] == 1
    assert output.exists()
