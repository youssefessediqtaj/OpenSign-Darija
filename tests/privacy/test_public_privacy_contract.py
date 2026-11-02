from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_public_recognition_contract_has_no_raw_media_fields() -> None:
    contract = json.loads(
        (ROOT / "packages/contracts/recognition-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    properties = contract["$defs"]["WordRecognitionRequest"]["properties"]
    forbidden = {
        "raw_video",
        "video",
        "image",
        "screenshot",
        "canvas",
        "base64",
        "audio",
        "microphone_audio",
    }

    assert forbidden.isdisjoint(properties)


def test_frontend_uses_same_origin_api_gateway_only() -> None:
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "apps/web/src").rglob("*")
        if path.suffix in {".ts", ".tsx"} and "node_modules" not in path.parts
    )

    assert "http://inference" not in source_text
    assert "http://speech" not in source_text
    assert "/predict/word" not in source_text
    assert "/synthesize" not in source_text
    assert "/api/v1/recognitions/colors-experimental" in source_text
    assert "/api/v1/recognitions/word" not in source_text
    assert "/api/v1/speech/sign" in source_text


def test_contribution_collection_defaults_fail_closed_without_legal_placeholders() -> None:
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "CONTRIBUTION_COLLECTION_ENABLED=false" in example
    assert "CONTRIBUTION_REFERENCE_VIDEOS_APPROVED=false" in example
    for variable in (
        "DATA_CONTROLLER_NAME",
        "DATA_CONTROLLER_ADDRESS",
        "DATA_CONTROLLER_CONTACT",
        "DATA_PROCESSING_PURPOSE",
        "DATA_RECIPIENT_CATEGORIES",
        "DATA_RETENTION_DAYS",
        "DATA_RIGHTS_CONTACT",
        "CNDP_PROCEDURE_TYPE",
        "CNDP_RECEIPT_OR_AUTHORIZATION_REFERENCE",
        "CONSENT_NOTICE_VERSION",
    ):
        assert f"{variable}=\n" in example


def test_contribution_video_paths_and_exports_exclude_direct_identifiers() -> None:
    service = (ROOT / "services/api/app/services/contribution_service.py").read_text(
        encoding="utf-8"
    )
    cli = (ROOT / "services/api/app/cli/contributions.py").read_text(encoding="utf-8")
    repository = (
        ROOT / "services/api/app/storage/contribution_repository.py"
    ).read_text(encoding="utf-8")
    assert 'object_key = f"pending/{contribution_id}/{contribution_id}.webm"' in service
    manifest_block = cli.split("manifest.append(", 1)[1].split(
        "(staging / \"manifest.json\")", 1
    )[0]
    assert "full_name" not in manifest_block
    assert '"city"' not in manifest_block
    assert '"age"' not in manifest_block
    export_query = repository.split("def list_exportable", 1)[1].split(
        "def retention_candidates", 1
    )[0]
    assert "c.deletion_status = 'ACTIVE'" in export_query
    assert "v.processing_eligibility = 1" in export_query


def test_contribution_storage_is_not_publicly_served_or_model_coupled() -> None:
    nginx = (ROOT / "infrastructure/nginx/default.conf").read_text(encoding="utf-8")
    assert "var/contributions" not in nginx
    assert "reference-signs" not in nginx
    contribution_source = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (
            ROOT / "services/api/app/api/v1",
            ROOT / "services/api/app/services",
            ROOT / "services/api/app/storage",
        )
        for path in root.glob("*contribution*.py")
    )
    assert "ml.training" not in contribution_source
    assert "onnx" not in contribution_source.lower()
    assert "inference_service" not in contribution_source
    assert "speech_service" not in contribution_source
