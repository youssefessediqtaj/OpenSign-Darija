from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ml.datasets.alphabet.manifest_builder import build_manifest as build_alphabet_manifest
from ml.datasets.external.import_local_archive import import_archive
from ml.datasets.external.registry import (
    list_sources,
    load_registry,
    validate_no_duplicate_documentation_sources,
)
from ml.datasets.external.safe_archive import safe_extract_zip
from ml.datasets.external.validate_licenses import validate
from ml.datasets.mosl_words.label_normalizer import normalize_arabic_label


def test_registry_keeps_sciencedirect_as_documentation_only() -> None:
    registry = load_registry()
    assert "mendeley_mosl_v1" in {source["id"] for source in registry["sources"]}
    assert "sciencedirect_mosl_article" in {
        source["id"] for source in registry["documentation_sources"]
    }
    validate_no_duplicate_documentation_sources()


def test_license_gate_blocks_unverified_kaggle() -> None:
    report = validate()
    by_id = {item["id"]: item for item in report["sources"]}
    assert by_id["mendeley_mosl_v1"]["allowed_for_training"] is True
    assert by_id["kaggle_moroccan_lsm_alphabet"]["allowed_for_training"] is False
    assert any(not source.enabled for source in list_sources() if source.id.startswith("kaggle"))


def test_safe_archive_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.txt", "no")
    try:
        safe_extract_zip(archive, tmp_path / "out")
    except ValueError as exc:
        assert "unsafe" in str(exc)
    else:
        raise AssertionError("path traversal archive must be rejected")


def test_mendeley_local_archive_import_fixture(tmp_path: Path) -> None:
    archive = tmp_path / "mosl.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("word/sample.txt", "fixture")
    report = import_archive("mendeley_mosl_v1", archive, tmp_path / "mendeley")
    assert report["file_count"] == 1
    assert (tmp_path / "mendeley" / "import-report.json").exists()
    stored = json.loads((tmp_path / "mendeley" / "import-report.json").read_text())
    assert stored["raw_immutable"] is True


def test_alphabet_manifest_preserves_unreviewed_label_and_relative_path(tmp_path: Path) -> None:
    image = tmp_path / "mystery" / "sample.png"
    image.parent.mkdir()
    image.write_bytes(b"not really an image")
    output = tmp_path / "manifest.csv"
    rows = build_alphabet_manifest(tmp_path, output)
    assert rows[0]["relative_path"] == "mystery/sample.png"
    assert rows[0]["review_status"] == "REQUIRES_LINGUISTIC_REVIEW"
    assert rows[0]["license"] == "UNCONFIRMED"


def test_arabic_label_normalization_keeps_original_decision_separate() -> None:
    assert normalize_arabic_label("  إختبار  ") == "اختبار"
