from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ml.datasets.colors_v1.validate import validate

ROOT = Path(__file__).resolve().parents[2]


def config() -> dict:
    return json.loads((ROOT / "ml/configs/colors_v1.json").read_text())


def sample(name: str, variant: str = "blue_variant_01") -> dict:
    return {"video_id": name, "semantic_label": "blue", "sign_variant_id": variant,
            "file_path": name + ".mp4", "source_type": "original_recording",
            "lineage_group_id": name, "license": "permission documented",
            "consent_status": "approved", "provenance": "local recording",
            "linguistic_review_status": "APPROVED", "split": "unassigned"}


def test_placeholders_blue_variants_and_empty_dataset(tmp_path: Path) -> None:
    labels = config()["labels"]
    assert len(labels) == 9 and sum(len(label["variants"]) for label in labels) == 10
    assert next(x for x in labels if x["id"] == "blue")["variants"] == ["blue_variant_01", "blue_variant_02"]
    result = validate(config(), [], tmp_path)
    assert not result["training_ready"] and not result["preprocessing_ready"]
    assert result["total_videos"] == 0


def test_validates_variants_duplicates_and_lineage_splits(tmp_path: Path) -> None:
    (tmp_path / "a.mp4").write_bytes(b"same")
    (tmp_path / "b.mp4").write_bytes(b"same")
    a, b = sample("a"), sample("b", "blue_variant_02")
    a.update(split="train", signer_id="signer")
    b.update(split="test", signer_id="signer", lineage_group_id="a")
    report = validate(config(), [a, b], tmp_path, inspect_media=False)
    assert any("duplicate bytes" in error for error in report["errors"])
    assert any("lineage_group_id" in error for error in report["errors"])
    assert any("signer_id" in error for error in report["errors"])
    assert not report["training_ready"]


def test_derived_parent_mismatch_missing_and_unsafe_paths(tmp_path: Path) -> None:
    (tmp_path / "a.mp4").write_bytes(b"a")
    a, b = sample("a"), sample("b")
    b.update(source_type="synthetic_character_replacement", source_video_id="a",
             lineage_group_id="different", transformation_type="replacement", file_path="../outside.mp4")
    report = validate(config(), [a, b], tmp_path, inspect_media=False)
    assert any("parent label, variant, or lineage" in error for error in report["errors"])
    assert any("traverse" in error for error in report["errors"])
    a["semantic_label"] = "not_a_color"
    assert any("unknown label" in error for error in validate(config(), [a], tmp_path, inspect_media=False)["errors"])


def test_legacy_root_rejected_before_reading() -> None:
    legacy = ROOT / "ml/data/external/mosl-video-dataset"
    with pytest.raises(ValueError, match="isolated"):
        validate(config(), [], legacy)


def test_media_probe_and_pending_review(tmp_path: Path) -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg not installed")
    video = tmp_path / "fixture.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=32x32:r=5:d=1",
                    "-c:v", "mpeg4", str(video)], check=True)
    record = sample("fixture", "blue_variant_02")
    record["linguistic_review_status"] = "PENDING_REVIEW"
    report = validate(config(), [record], tmp_path)
    assert not report["errors"] and report["records"][0]["width"] == 32
    assert not report["preprocessing_ready"]
    record["linguistic_review_status"] = "APPROVED"
    report = validate(config(), [record], tmp_path)
    assert report["media_review_ready"] and not report["preprocessing_ready"]
    assert not report["training_ready"]


def test_unknown_decisions_and_measured_metrics() -> None:
    from ml.evaluation.colors_v1 import decide, evaluate

    assert decide("blue", 0.99, None)["status"] == "UNKNOWN_SIGN"
    assert decide("blue", 0.7, 0.8)["label"] is None
    assert decide("blue", 0.9, 0.8)["calibrated"] is False
    result = evaluate(["blue", "blue", None, None], ["blue", None, "blue", None], ["blue"])
    assert result["known_sign_recall"] == 0.5
    assert result["false_rejection_rate"] == 0.5
    assert result["false_acceptance_rate"] == 0.5
    assert result["unknown_rejection_rate"] == 0.5
    assert result["per_class"]["blue"]["f1"] == 0.5
    with pytest.raises(ValueError):
        decide("blue", float("nan"), None)


def test_python_normalization_matches_shared_numeric_fixture() -> None:
    import numpy as np

    from ml.preprocessing.landmark_schema_v1 import normalize_frame

    fixture = json.loads((ROOT / "apps/web/src/features/recognition/tests/colors-normalization-fixture.json").read_text())
    groups = []
    for name, count in (("pose", 33), ("left_hand", 21), ("right_hand", 21)):
        group = np.full((count, 3), np.nan, dtype=np.float32)
        for index, value in fixture[name].items():
            group[int(index)] = value
        groups.append(group)
    result = normalize_frame(*groups)
    for index, expected in fixture["expected"].items():
        np.testing.assert_allclose(result.landmarks[int(index)], expected, atol=1e-6)
        assert result.presence_mask[int(index)] == 1
    assert result.presence_mask[0] == 0
    assert not result.landmarks[0].any()


def test_grouped_split_is_deterministic_and_signer_disjoint() -> None:
    from ml.datasets.colors_v1.splits import grouped_split

    records = []
    for signer in range(5):
        for variant in ("blue_variant_01", "blue_variant_02"):
            item = sample(f"s{signer}-{variant}", variant)
            item.update(signer_id=f"s{signer}", lineage_group_id=f"s{signer}-{variant}")
            records.append(item)
    result = grouped_split(records, seed=17)
    assert result == grouped_split(records, seed=17)
    assignments = result["assignments"]
    assert set(assignments.values()) == {"train", "validation", "test"}
    for signer in range(5):
        assert len({assignments[r["video_id"]] for r in records if r["signer_id"] == f"s{signer}"}) == 1
    records[0]["signer_id"] = None
    with pytest.raises(ValueError, match="signer required"):
        grouped_split(records)


def test_private_report_never_overwrites_or_writes_among_videos(tmp_path: Path) -> None:
    from ml.datasets.colors_v1.validate import write_private_report

    videos = tmp_path / "videos"
    videos.mkdir()
    report = tmp_path / "report.json"
    write_private_report(report, "{}", videos)
    assert report.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_private_report(report, "changed", videos)
    assert report.read_text() == "{}"
    with pytest.raises(ValueError, match="outside"):
        write_private_report(videos / "report.json", "{}", videos)


def test_temporal_sampling_matches_browser_fixtures() -> None:
    from ml.datasets.colors_v1.preprocess import sample_indices

    fixture = json.loads((ROOT / "apps/web/src/features/recognition/tests/colors-sequence-fixture.json").read_text())
    for item in fixture:
        assert sample_indices(item["count"], item["target"]).tolist() == item["indices"]
    with pytest.raises(ValueError):
        sample_indices(0)


def test_template_baseline_fails_closed_and_checks_provenance(tmp_path: Path) -> None:
    import numpy as np

    from ml.datasets.colors_v1.baseline import fit, load, predict
    from ml.datasets.colors_v1.preprocess import FEATURE_VERSION

    features = tmp_path / "features"
    features.mkdir()
    item = sample("fixture", "blue_variant_02")
    item.update(file_hash="abc", linguistic_review_status="PENDING_REVIEW",
                local_experimental_training_permission="owner_confirmed")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([item]))
    landmarks = np.full((60, 75, 3), 0.5, dtype=np.float32)
    mask = np.ones((60, 75), dtype=np.float32)
    meta = {"feature_version": FEATURE_VERSION, "video_id": "fixture", "source_sha256": "abc",
            "semantic_label": "blue", "sign_variant_id": "blue_variant_02"}
    np.savez(features / "fixture.npz", landmarks=landmarks, presence_mask=mask, metadata=json.dumps(meta))
    path = tmp_path / "model.npz"
    with pytest.raises(ValueError, match="pending"):
        fit(manifest, features, path)
    assert fit(manifest, features, path, allow_pending_review=True)["status"] == "EXPERIMENTAL_NOT_VALIDATED"
    model = load(path)
    assert predict(model, landmarks, mask)["status"] == "UNKNOWN_SIGN"
    accepted = predict(model, landmarks, mask, max_distance=0)
    assert accepted["semantic_label"] == "blue" and accepted["variant"] == "blue_variant_02"
    assert not accepted["calibrated"]
    assert predict(model, landmarks, mask, max_distance=0, source_frame_count=2)["status"] == "INSUFFICIENT_FRAMES"
    empty = mask.copy()
    empty[:, 33:] = 0
    assert predict(model, landmarks, empty)["status"] == "NO_HAND_DETECTED"
    with pytest.raises(FileExistsError):
        fit(manifest, features, path, allow_pending_review=True)


def test_source_archive_import_validates_mapping_hashes_and_privacy(tmp_path: Path) -> None:
    import csv
    import hashlib
    import io
    import zipfile

    from ml.datasets.colors_v1.import_sources import FILES, import_archive

    table = io.StringIO()
    writer = csv.DictWriter(table, fieldnames=["file_path", "semantic_label", "sign_variant_id", "lineage_group_id"])
    writer.writeheader()
    checksums = []
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        for name, (label, variant) in FILES.items():
            key = f"videos/{name}"
            payload = f"fixture-{name}".encode()
            zipped.writestr(key, payload)
            checksums.append(f"{hashlib.sha256(payload).hexdigest()}  {key}")
            writer.writerow({"file_path": key, "semantic_label": label, "sign_variant_id": variant,
                             "lineage_group_id": variant})
        zipped.writestr("source_manifest.csv", table.getvalue())
        zipped.writestr("README.txt", "fixture")
        zipped.writestr("SHA256SUMS.txt", "\n".join(checksums))
    target = tmp_path / "dataset"
    assert import_archive(archive, target)["imported"] == 10
    records = json.loads((target / "manifest.json").read_text())
    assert all(x["local_experimental_training_permission"] == "UNCONFIRMED" for x in records)
    assert all(x["consent_status"] == "pending" for x in records)
    assert (target / "videos/Bleu.mov").stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        import_archive(archive, target)
    with zipfile.ZipFile(archive, "a") as zipped:
        zipped.writestr("../escape.mov", b"x")
    with pytest.raises(ValueError, match="archive members"):
        import_archive(archive, tmp_path / "unsafe")


def test_video_timestamps_are_monotonic(tmp_path: Path) -> None:
    from ml.datasets.colors_v1.preprocess import frame_timestamps

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg not installed")
    path = tmp_path / "timestamps.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=32x32:r=5:d=1",
                    "-c:v", "mpeg4", str(path)], check=True)
    times = frame_timestamps(path)
    assert len(times) == 5
    assert all(a < b for a, b in zip(times, times[1:]))


def test_model_not_ready_and_gru_export_smoke(tmp_path: Path) -> None:
    import numpy as np

    from ml.datasets.colors_v1.baseline import predict_from_package
    from ml.datasets.colors_v1.preprocess import FEATURE_VERSION
    from ml.datasets.colors_v1.train_smoke import train

    empty = np.zeros((60, 75, 3), dtype=np.float32)
    mask = np.ones((60, 75), dtype=np.float32)
    assert predict_from_package(tmp_path / "missing.npz", empty, mask)["status"] == "MODEL_NOT_READY"
    package = tmp_path / "templates.npz"
    meta = {"status": "EXPERIMENTAL_NOT_VALIDATED", "feature_version": FEATURE_VERSION,
            "manifest_sha256": "synthetic-fixture"}
    np.savez(package, templates=np.stack([empty, empty + 0.1]), masks=np.stack([mask, mask]),
             labels=np.array(["blue", "red"]), variants=np.array(["blue_variant_01", "red_variant_01"]),
             metadata=json.dumps(meta))
    output = tmp_path / "experiment"
    result = train(package, output, epochs=1)
    assert result["status"] == "SMOKE_ONLY_NOT_VALIDATED"
    assert result["onnx_parity_max_abs_error"] < 1e-5
    assert (output / "checkpoint.pt").is_file() and (output / "model.onnx").is_file()
    with pytest.raises(FileExistsError):
        train(package, output)


def test_python_sequence_normalization_matches_browser_fixture() -> None:
    import numpy as np

    from ml.datasets.colors_v1.preprocess import sample_indices
    from ml.preprocessing.landmark_schema_v1 import normalize_frame

    fixture = json.loads((ROOT / "apps/web/src/features/recognition/tests/colors-sequence-values.json").read_text())
    frames = []
    for x in fixture["hand_x"]:
        pose = np.full((33, 3), np.nan, dtype=np.float32)
        left = np.full((21, 3), np.nan, dtype=np.float32)
        right = np.full((21, 3), np.nan, dtype=np.float32)
        pose[11] = [0.25, 0.5, 0]
        pose[12] = [0.75, 0.5, 0]
        left[0] = [x, 0.5, 0]
        frames.append(normalize_frame(pose, left, right))
    indices = sample_indices(len(frames), 5)
    assert indices.tolist() == fixture["expected_indices"]
    np.testing.assert_allclose([frames[i].landmarks[33, 0] for i in indices],
                               fixture["expected_normalized_hand_x"], atol=1e-6)
    assert all(frames[i].presence_mask[54] == 0 for i in indices)


def test_held_out_evaluation_requires_disjoint_known_sources() -> None:
    from ml.evaluation.colors_v1 import evaluation_report

    train_rows = [{"lineage_group_id": "source-1", "signer_id": "signer-1", "file_hash": "aaa"}]
    evaluated = [{"actual": "blue", "predicted": "blue", "lineage_group_id": "source-2",
                  "signer_id": "signer-2", "file_hash": "bbb"}]
    report = evaluation_report(evaluated, ["blue"], split="held_out_test", training_records=train_rows)
    assert report["metrics"]["sample_count"] == 1
    assert report["signer_independence"] == "metadata_disjoint_unverified"
    evaluated[0]["signer_id"] = "signer-1"
    with pytest.raises(ValueError, match="overlaps"):
        evaluation_report(evaluated, ["blue"], split="held_out_test", training_records=train_rows)
    evaluated[0]["signer_id"] = None
    with pytest.raises(ValueError, match="required"):
        evaluation_report(evaluated, ["blue"], split="held_out_test", training_records=train_rows)


def test_review_requires_separate_identified_approvals() -> None:
    from ml.datasets.colors_v1.review import validate_review

    source = {"video_id": "blue_variant_01", "file_hash": "abc"}
    review = {"video_id": "blue_variant_01", "source_sha256": "abc", "sign_start_time": None,
              "sign_end_time": None, "technical_review_status": "PENDING", "linguistic_review_status": "PENDING"}
    validate_review(review, source)
    review.update(technical_review_status="APPROVED", sign_start_time=1.0, sign_end_time=2.0)
    with pytest.raises(ValueError, match="reviewer and date"):
        validate_review(review, source)
    review.update(technical_reviewer="operator", technical_review_date="2026-11-01")
    validate_review(review, source)
    review["linguistic_review_status"] = "APPROVED"
    with pytest.raises(ValueError, match="qualified reviewer"):
        validate_review(review, source)
    review["source_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash"):
        validate_review(review, source)


def test_experimental_model_registry_requires_compatible_labels_and_shapes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from ml.datasets.colors_v1.registry import FEATURE_VERSION, LABELS, register

    directory = tmp_path / "model"
    directory.mkdir()
    (directory / "checkpoint.pt").write_bytes(b"checkpoint")
    (directory / "model.onnx").write_bytes(b"onnx")
    report = {"dataset": "colors_v1", "status": "SMOKE_ONLY_NOT_VALIDATED", "feature_version": FEATURE_VERSION,
              "labels": LABELS, "activation": "DISABLED", "calibration": "UNAVAILABLE", "manifest_sha256": "fixture",
              "epochs": 1, "seed": 42, "hidden_size": 16}
    (directory / "report.json").write_text(json.dumps(report))

    class Session:
        def get_inputs(self) -> list:
            return [SimpleNamespace(name="landmarks", shape=["batch", 60, 75, 3], type="tensor(float)")]

        def get_outputs(self) -> list:
            return [SimpleNamespace(name="logits", shape=["batch", 9])]

    monkeypatch.setattr("ml.datasets.colors_v1.registry.ort.InferenceSession", lambda *args, **kwargs: Session())
    output = tmp_path / "registry.json"
    assert register(directory, output)["activation_status"] == "INACTIVE"
    with pytest.raises(FileExistsError):
        register(directory, output)
    report["labels"] = list(reversed(LABELS))
    (directory / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="metadata"):
        register(directory, tmp_path / "wrong.json")


def test_calibration_and_promotion_fail_closed() -> None:
    from ml.evaluation.colors_v1 import calibration_readiness, promotion_readiness

    empty = calibration_readiness([], [], [])
    assert not empty["ready_to_design_calibration"] and empty["threshold"] is None
    assert any("unknown validation" in item for item in empty["blockers"])
    result = promotion_readiness({})
    assert not result["eligible_for_manual_review"] and result["activation_status"] == "INACTIVE"
    assert "independent_evaluation_complete" in result["missing"]


def test_derived_registration_stays_pending_and_preserves_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ml.datasets.colors_v1.extend_manifest import extend

    root = tmp_path / "videos"
    root.mkdir()
    base, additions, config_path = (tmp_path / name for name in ("base.json", "new.json", "config.json"))
    original = sample("original")
    child = sample("child")
    child.update(source_type="synthetic_character_replacement", source_video_id="original",
                 transformation_type="character replacement", lineage_group_id="original",
                 linguistic_review_status="PENDING_REVIEW")
    base.write_text(json.dumps([original]))
    additions.write_text(json.dumps([child]))
    config_path.write_text(json.dumps(config()))
    monkeypatch.setattr("ml.datasets.colors_v1.extend_manifest.validate", lambda *args: {"errors": []})
    result = tmp_path / "result.json"
    assert extend(base, additions, config_path, root, result) == 1
    assert len(json.loads(base.read_text())) == 1
    assert json.loads(result.read_text())[1]["linguistic_review_status"] == "PENDING_REVIEW"
    child["linguistic_review_status"] = "APPROVED"
    additions.write_text(json.dumps([child]))
    with pytest.raises(ValueError, match="pending"):
        extend(base, additions, config_path, root, tmp_path / "not-allowed.json")


def test_timestamp_rejection_and_left_right_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    import numpy as np

    from ml.datasets.colors_v1.preprocess import frame_timestamps, sample_indices
    from ml.preprocessing.landmark_schema_v1 import normalize_frame

    class Response:
        stdout = json.dumps({"frames": [{"best_effort_timestamp_time": "0.2"}, {"best_effort_timestamp_time": "0.1"}]})

    monkeypatch.setattr("ml.datasets.colors_v1.preprocess.subprocess.run", lambda *a, **kw: Response())
    with pytest.raises(ValueError, match="not monotonic"):
        frame_timestamps(Path("unused"))
    pose = np.full((33, 3), np.nan, dtype=np.float32)
    pose[11], pose[12] = [0.25, 0.5, 0], [0.75, 0.5, 0]
    left = np.full((21,3), np.nan, dtype=np.float32)
    right = np.full((21,3), np.nan, dtype=np.float32)
    left[0], right[0] = [0.3, 0.4, 0], [0.7, 0.4, 0]
    frame = normalize_frame(pose, left, right)
    swapped = normalize_frame(pose, right, left)
    assert frame.landmarks[33, 0] < 0 < frame.landmarks[54, 0]
    assert swapped.landmarks[33, 0] > 0 > swapped.landmarks[54, 0]
    mirrored_pose, mirrored_left, mirrored_right = pose.copy(), left.copy(), right.copy()
    mirrored_pose[:, 0] = 1 - mirrored_pose[:, 0]
    mirrored_left[:, 0] = 1 - mirrored_left[:, 0]
    mirrored_right[:, 0] = 1 - mirrored_right[:, 0]
    mirrored = normalize_frame(mirrored_pose, mirrored_left, mirrored_right)
    assert np.isclose(mirrored.landmarks[33, 0], -frame.landmarks[33, 0])
    assert np.isclose(mirrored.landmarks[54, 0], -frame.landmarks[54, 0])
    assert np.allclose(np.linspace(0, 1, 5)[sample_indices(5, 3)], np.linspace(0, 1, 9)[sample_indices(9, 3)])
