from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_recognition_contract_is_closed_and_shape_pinned() -> None:
    contract = json.loads(
        (ROOT / "packages/contracts/recognition-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    request = contract["$defs"]["WordRecognitionRequest"]
    frame = contract["$defs"]["Frame"]
    landmark = contract["$defs"]["Landmark"]

    assert request["additionalProperties"] is False
    assert request["properties"]["feature_schema_version"]["const"] == (
        "OPEN_SIGNE_LANDMARK_SCHEMA_V1"
    )
    assert request["properties"]["frames"]["minItems"] == 60
    assert request["properties"]["frames"]["maxItems"] == 60
    assert frame["properties"]["landmarks"]["minItems"] == 75
    assert frame["properties"]["landmarks"]["maxItems"] == 75
    assert landmark["minItems"] == landmark["maxItems"] == 3


def test_speech_contract_accepts_label_keys_not_free_text() -> None:
    contract = json.loads(
        (ROOT / "packages/contracts/speech.schema.json").read_text(encoding="utf-8")
    )
    public_request = contract["$defs"]["PublicSignSpeechRequest"]

    assert public_request["additionalProperties"] is False
    assert set(public_request["required"]) == {"label_key"}
    assert "text" not in public_request["properties"]
