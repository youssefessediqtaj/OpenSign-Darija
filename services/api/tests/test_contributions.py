import json
import shutil
import sqlite3
import subprocess
from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.services.contribution_validation import ProbedVideo, validate_staged_video
from app.storage.contribution_repository import ContributionRepository
from app.storage.video_storage import VideoStorageError

VALID_WEBM = b"\x1a\x45\xdf\xa3" + b"private-video-test" * 8


def test_blank_retention_environment_value_keeps_disabled_api_bootable() -> None:
    settings = Settings.model_validate({"data_retention_days": ""})
    assert settings.data_retention_days is None
    assert settings.contribution_collection_enabled is False


def test_real_webm_is_probed_and_fully_decoded(tmp_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("FFmpeg tooling is unavailable")
    video = tmp_path / "real-test.webm"
    generated = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=teal:s=320x240:r=15",
            "-t",
            "2.2",
            "-c:v",
            "libvpx",
            "-an",
            str(video),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert generated.returncode == 0, generated.stderr
    metadata = validate_staged_video(
        video,
        declared_mime_type="video/webm",
        settings=Settings(
            contribution_ffmpeg_path=ffmpeg,
            contribution_ffprobe_path=ffprobe,
        ),
        expected_min_duration_seconds=2,
        expected_max_duration_seconds=10,
    )
    assert metadata.duration_seconds == pytest.approx(2.2, abs=0.15)
    assert (metadata.width, metadata.height) == (320, 240)
    assert metadata.frame_rate == pytest.approx(15)
    assert len(metadata.sha256) == 64


@pytest.fixture
def enabled_collection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Path]:
    values = {
        "CONTRIBUTION_COLLECTION_ENABLED": "true",
        "CONTRIBUTION_REFERENCE_VIDEOS_APPROVED": "true",
        "DATA_CONTROLLER_NAME": "OpenSigne Test Controller",
        "DATA_CONTROLLER_ADDRESS": "Test controller address",
        "DATA_CONTROLLER_CONTACT": "controller@example.test",
        "DATA_PROCESSING_PURPOSE": (
            "améliorer et évaluer la reconnaissance de la langue des signes marocaine"
        ),
        "DATA_RECIPIENT_CATEGORIES": "équipe modèle;collaborateurs autorisés",
        "DATA_MODEL_COLLABORATOR_SHARING": "Collaborateurs contractuellement autorisés uniquement.",
        "DATA_STORAGE_LOCATION_CATEGORY": "Infrastructure privée contrôlée",
        "DATA_RETENTION_DAYS": "30",
        "DATA_RIGHTS_CONTACT": "rights@example.test",
        "CNDP_PROCEDURE_TYPE": "declaration",
        "CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE": "TEST-ONLY-NOT-A-REAL-REFERENCE",
        "CONSENT_NOTICE_VERSION": "test-notice-v1",
        "CONTRIBUTION_STORAGE_ROOT": str(tmp_path / "private-contributions"),
        "CONTRIBUTION_DATABASE_PATH": str(tmp_path / "private-contributions/metadata/db.sqlite3"),
        "CONTRIBUTION_MIN_VIDEO_BYTES": "4",
        "CONTRIBUTION_MAX_VIDEO_BYTES": "10000",
        "CONTRIBUTION_RATE_LIMIT": "100",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield tmp_path / "private-contributions"
    get_settings.cache_clear()


@pytest.fixture
def valid_video_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.contribution_validation.probe_and_decode_video",
        lambda path, settings: ProbedVideo(
            duration_seconds=3.0,
            width=640,
            height=480,
            frame_rate=30.0,
        ),
    )


def valid_form(**overrides: object) -> dict[str, str]:
    fields = {
        "full_name": "Personne Test",
        "age": "29",
        "city": "Rabat",
        "sign_key": "salam",
        "consent_accepted": "true",
        "consent_notice_version": "test-notice-v1",
    }
    fields.update({key: str(value) for key, value in overrides.items()})
    return fields


def post_contribution(
    client: TestClient,
    *,
    fields: dict[str, str] | None = None,
    content: bytes = VALID_WEBM,
    mime_type: str = "video/webm",
    filename: str = "capture.webm",
):
    return client.post(
        "/api/v1/contributions",
        data=fields or valid_form(),
        files={"video": (filename, content, mime_type)},
    )


def test_collection_is_fail_closed_by_default(client: TestClient) -> None:
    get_settings.cache_clear()
    status = client.get("/api/v1/contributions/status")
    assert status.status_code == 200
    assert status.json()["collection_enabled"] is False
    assert status.json()["public_submission_allowed"] is False
    assert status.json()["storage_status"] == "not_checked"
    assert status.json()["message"] == "La collecte des contributions n’est pas encore ouverte."
    notice = client.get("/api/v1/contributions/notice")
    assert notice.status_code == 200
    assert "Aucune donnée de contribution n’est recueillie" in notice.json()["summary"]
    blocked = post_contribution(client)
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == "CONTRIBUTION_COLLECTION_CLOSED"


def test_exact_server_controlled_catalog_and_unapproved_video_state(
    client: TestClient,
) -> None:
    get_settings.cache_clear()
    response = client.get("/api/v1/contributions/signs")
    assert response.status_code == 200
    body = response.json()
    assert [sign["key"] for sign in body] == [
        "salam",
        "chokran",
        "tabib",
        "mosaada",
        "maa",
    ]
    assert [sign["label_ar"] for sign in body] == ["سلام", "شكرا", "طبيب", "مساعدة", "ماء"]
    assert all(sign["reference_video_url"] is None for sign in body)
    assert all(sign["reference_video_approved"] is False for sign in body)


def test_missing_cndp_reference_keeps_submission_closed(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONTRIBUTION_COLLECTION_ENABLED", "true")
    monkeypatch.setenv("CONTRIBUTION_REFERENCE_VIDEOS_APPROVED", "true")
    monkeypatch.setenv("DATA_CONTROLLER_NAME", "Controller")
    monkeypatch.setenv("DATA_CONTROLLER_ADDRESS", "Address")
    monkeypatch.setenv("DATA_CONTROLLER_CONTACT", "Contact")
    monkeypatch.setenv("DATA_PROCESSING_PURPOSE", "Purpose")
    monkeypatch.setenv("DATA_RECIPIENT_CATEGORIES", "Recipients")
    monkeypatch.setenv("DATA_MODEL_COLLABORATOR_SHARING", "Controlled sharing")
    monkeypatch.setenv("DATA_STORAGE_LOCATION_CATEGORY", "Private Morocco storage")
    monkeypatch.setenv("DATA_RETENTION_DAYS", "30")
    monkeypatch.setenv("DATA_RIGHTS_CONTACT", "Rights")
    monkeypatch.setenv("CNDP_PROCEDURE_TYPE", "prior_authorization")
    monkeypatch.setenv("CONSENT_NOTICE_VERSION", "v1")
    monkeypatch.delenv("CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE", raising=False)
    get_settings.cache_clear()
    body = client.get("/api/v1/contributions/status").json()
    assert body["public_submission_allowed"] is False
    assert "CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE" in body["missing_configuration"]
    assert post_contribution(client).status_code == 503


def test_notice_contains_controller_purpose_retention_rights_and_cndp(
    client: TestClient,
    enabled_collection: Path,
) -> None:
    response = client.get("/api/v1/contributions/notice")
    assert response.status_code == 200
    body = response.json()
    assert body["controller_name"] == "OpenSigne Test Controller"
    assert "reconnaissance de la langue des signes marocaine" in body["purpose"]
    assert body["retention_days"] == 30
    assert body["rights_request_method"] == "rights@example.test"
    assert body["cndp_reference"] == "TEST-ONLY-NOT-A-REAL-REFERENCE"
    assert body["notice_version"] == "test-notice-v1"
    assert body["arabic_translation_status"] == "structure_ready_translation_pending"


def test_valid_adult_contribution_is_private_and_receipt_has_no_pii(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
) -> None:
    response = post_contribution(
        client,
        filename="../../Personne Test-Rabat.webm",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    contribution_id = UUID(body["contribution_id"])
    assert body == {
        "status": "received",
        "contribution_id": str(contribution_id),
        "sign_key": "salam",
        "created_at": body["created_at"],
        "consent_notice_version": "test-notice-v1",
        "review_status": "pending",
        "deletion_request_instructions": (
            "Conservez cette référence et contactez rights@example.test pour exercer vos droits."
        ),
    }
    private_files = list((enabled_collection / "pending").rglob("*.webm"))
    assert len(private_files) == 1
    assert private_files[0].name == f"{contribution_id}.webm"
    assert "Personne" not in str(private_files[0])
    assert "Rabat" not in str(private_files[0])
    assert private_files[0].stat().st_mode & 0o777 == 0o600

    database = enabled_collection / "metadata/db.sqlite3"
    with sqlite3.connect(database) as connection:
        contributor = connection.execute(
            "SELECT full_name, age, city, consent_timestamp FROM contributors"
        ).fetchone()
        video = connection.execute(
            "SELECT private_object_key, sha256, review_status, processing_eligibility "
            "FROM contribution_videos"
        ).fetchone()
    assert contributor[:3] == ("Personne Test", 29, "Rabat")
    assert contributor[3].endswith("+00:00")
    assert video[0] == f"pending/{contribution_id}/{contribution_id}.webm"
    assert video[2:] == ("PENDING", 0)
    assert database.stat().st_mode & 0o777 == 0o600

    receipt = client.get(f"/api/v1/contributions/{contribution_id}/receipt")
    assert receipt.status_code == 200
    serialized = receipt.text
    assert "Personne Test" not in serialized
    assert "Rabat" not in serialized
    assert "private_object_key" not in serialized
    assert "storage" not in serialized.lower()
    assert client.get(f"/api/v1/contributions/{contribution_id}/video").status_code == 404


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"age": 17}, "ADULTS_ONLY"),
        ({"consent_accepted": "false"}, "CONSENT_REQUIRED"),
        ({"consent_notice_version": "old"}, "OBSOLETE_NOTICE_VERSION"),
        ({"sign_key": "arbitrary"}, "UNKNOWN_SIGN"),
    ],
)
def test_invalid_identity_consent_or_sign_is_never_persisted(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
    overrides: dict[str, object],
    expected_code: str,
) -> None:
    response = post_contribution(client, fields=valid_form(**overrides))
    assert response.status_code in {409, 422}
    assert response.json()["error"]["code"] == expected_code
    assert not list(enabled_collection.rglob("*.webm"))
    database = enabled_collection / "metadata/db.sqlite3"
    if database.exists():
        with sqlite3.connect(database) as connection:
            assert connection.execute("SELECT COUNT(*) FROM contributors").fetchone()[0] == 0


def test_missing_video_and_unexpected_fields_are_rejected(
    client: TestClient,
    enabled_collection: Path,
) -> None:
    missing = client.post("/api/v1/contributions", data=valid_form())
    assert missing.status_code == 422
    response = post_contribution(
        client,
        fields={**valid_form(), "unexpected": "value"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"INVALID_MULTIPART", "INVALID_FORM_FIELDS"}


def test_video_validation_rejects_size_mime_signature_and_duration(
    client: TestClient,
    enabled_collection: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsupported = post_contribution(client, mime_type="video/mp4")
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_VIDEO_TYPE"

    malformed = post_contribution(client, content=b"not-a-webm")
    assert malformed.status_code == 415
    assert malformed.json()["error"]["code"] == "INVALID_VIDEO_SIGNATURE"

    oversized = post_contribution(client, content=VALID_WEBM + b"x" * 10000)
    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "VIDEO_TOO_LARGE"

    monkeypatch.setattr(
        "app.services.contribution_validation.probe_and_decode_video",
        lambda path, settings: ProbedVideo(1.0, 640, 480, 30.0),
    )
    too_short = post_contribution(client, content=VALID_WEBM + b"short")
    assert too_short.status_code == 422
    assert too_short.json()["error"]["code"] == "VIDEO_TOO_SHORT"

    monkeypatch.setattr(
        "app.services.contribution_validation.probe_and_decode_video",
        lambda path, settings: ProbedVideo(11.0, 640, 480, 30.0),
    )
    too_long = post_contribution(client, content=VALID_WEBM + b"long")
    assert too_long.status_code == 422
    assert too_long.json()["error"]["code"] == "VIDEO_TOO_LONG"
    assert not list(enabled_collection.rglob("*.webm"))


def test_duplicate_video_is_rejected_without_orphan(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
) -> None:
    first = post_contribution(client)
    second = post_contribution(
        client,
        fields=valid_form(full_name="Autre Personne", city="Fès"),
    )
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_CONTRIBUTION"
    assert len(list((enabled_collection / "pending").rglob("*.webm"))) == 1
    assert not list((enabled_collection / ".staging").glob("*"))


def test_storage_failure_returns_503_and_core_health_is_independent(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unavailable_root = enabled_collection.parent / "not-a-directory"
    unavailable_root.write_text("blocked", encoding="utf-8")
    monkeypatch.setenv("CONTRIBUTION_STORAGE_ROOT", str(unavailable_root))
    monkeypatch.setenv(
        "CONTRIBUTION_DATABASE_PATH",
        str(unavailable_root / "metadata/db.sqlite3"),
    )
    get_settings.cache_clear()
    response = post_contribution(client)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "CONTRIBUTION_STORAGE_UNAVAILABLE"

    async def healthy(url: str, timeout_seconds: float) -> str:
        return "healthy"

    monkeypatch.setattr("app.api.v1.system.service_health", healthy)
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_promote_failure_rolls_back_metadata_and_cleans_staging(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_promote(*args: object, **kwargs: object) -> None:
        raise VideoStorageError("test storage failure")

    monkeypatch.setattr(
        "app.storage.video_storage.LocalPrivateVideoStorage.promote",
        fail_promote,
    )
    response = post_contribution(client)
    assert response.status_code == 503
    database = enabled_collection / "metadata/db.sqlite3"
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM contributors").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM contribution_videos").fetchone()[0] == 0
    assert not list((enabled_collection / ".staging").glob("*"))
    assert not list((enabled_collection / "pending").rglob("*.webm"))


def test_withdrawal_deletion_and_export_eligibility_are_fail_closed(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
) -> None:
    first = post_contribution(client)
    contribution_id = first.json()["contribution_id"]
    repository = ContributionRepository(get_settings().contribution_database_file)
    assert repository.transition_review(
        contribution_id,
        "APPROVED_FOR_DATASET",
        actor="test-reviewer",
        reason="test checks complete",
    )
    exportable = repository.list_exportable()
    assert len(exportable) == 1
    assert "full_name" not in exportable[0]
    assert "city" not in exportable[0]
    assert repository.request_withdrawal(contribution_id, actor="test-rights-operator")
    assert repository.list_exportable() == []
    assert repository.mark_deleted(
        contribution_id,
        actor="test-rights-operator",
        reason="verified deletion request",
    )
    with sqlite3.connect(enabled_collection / "metadata/db.sqlite3") as connection:
        row = connection.execute(
            "SELECT full_name, age, city, deletion_status FROM contributors"
        ).fetchone()
        video = connection.execute(
            "SELECT processing_eligibility FROM contribution_videos"
        ).fetchone()
    assert row == (None, None, None, "DELETED")
    assert video == (0,)


def test_retention_candidates_are_reportable_without_automatic_deletion(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
) -> None:
    response = post_contribution(client)
    contribution_id = response.json()["contribution_id"]
    database = enabled_collection / "metadata/db.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE contribution_videos SET created_at = '2020-01-01T00:00:00+00:00'"
        )
        connection.commit()
    repository = ContributionRepository(get_settings().contribution_database_file)
    candidates = repository.retention_candidates(30)
    assert [row["contribution_id"] for row in candidates] == [contribution_id]
    assert repository.get_receipt(contribution_id) is not None


def test_retention_report_omits_private_storage_keys(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from app.cli import contributions as contributions_cli

    response = post_contribution(client)
    contribution_id = response.json()["contribution_id"]
    database = enabled_collection / "metadata/db.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE contribution_videos SET created_at = '2020-01-01T00:00:00+00:00'"
        )
        connection.commit()
    report_root = tmp_path / "retention-reports"
    monkeypatch.setattr(contributions_cli, "REPORT_ROOT", report_root)

    result = contributions_cli.command_retention(Namespace(execute=False))

    assert result == 0
    report_path = next(report_root.glob("contributions-retention-*.json"))
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["candidates"][0]["contribution_id"] == contribution_id
    assert "private_object_key" not in report_text


def test_rate_limit_is_separate_from_recognition(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.contribution_request_protection import clear_contribution_rate_limits

    monkeypatch.setenv("CONTRIBUTION_RATE_LIMIT", "1")
    get_settings.cache_clear()
    clear_contribution_rate_limits()
    first = post_contribution(client)
    second = post_contribution(client, content=VALID_WEBM + b"different")
    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "RATE_LIMITED"


def test_cross_origin_submission_is_rejected_before_upload(
    client: TestClient,
    enabled_collection: Path,
    valid_video_probe: None,
) -> None:
    response = client.post(
        "/api/v1/contributions",
        data=valid_form(),
        files={"video": ("capture.webm", VALID_WEBM, "video/webm")},
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"
    assert not list(enabled_collection.rglob("*.webm"))
