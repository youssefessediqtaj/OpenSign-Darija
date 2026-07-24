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
    assert "/api/v1/recognitions/word" in source_text
    assert "/api/v1/speech/sign" in source_text
