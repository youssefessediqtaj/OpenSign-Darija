"""Synthetic tones exercise the pipeline; they are never Darija recordings."""

import importlib.util
import json
import math
import struct
import wave
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "voice_pack",
    Path(__file__).resolve().parents[2] / "scripts/speech/prepare_voice_pack.py",
)
voice_pack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice_pack)


def tone(path, *, amplitude=10000, seconds=0.5, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(
            b"".join(
                struct.pack(
                    "<h", int(amplitude * math.sin(2 * math.pi * 440 * i / rate))
                )
                for i in range(int(seconds * rate))
            )
        )


def test_conversion_missing_and_approval_gate(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    tone(src / "red.wav")
    staging = tmp_path / "private"
    report = voice_pack.prepare(src, staging)
    assert report["assets"]["red"]["issues"] == []
    assert report["assets"]["blue"]["issues"] == ["missing_or_symlink"]
    with wave.open(str(staging / "red.wav")) as wav:
        assert wav.getframerate() == 24000
    approval = tmp_path / "private-review.json"
    approval.write_text(
        json.dumps(
            {
                "assets": {
                    "red": {"sha256": report["assets"]["red"]["sha256"], "version": "1"}
                }
            }
        )
    )
    with pytest.raises(ValueError):
        voice_pack.package(staging, approval, tmp_path / "pack")
    entry = {
        "sha256": report["assets"]["red"]["sha256"],
        "version": "1",
        "text_approved": True,
        "audio_approved": True,
        "rights_approved": True,
        "expression": "حمر",
        "review_reference": "private-1",
        "rights_reference": "private-2",
    }
    approval.write_text(json.dumps({"assets": {"red": entry}}))
    assert voice_pack.package(staging, approval, tmp_path / "pack")["assets"]["red"][
        "approved"
    ]
    entry["sha256"] = "0" * 64
    approval.write_text(json.dumps({"assets": {"red": entry}}))
    with pytest.raises(ValueError):
        voice_pack.package(staging, approval, tmp_path / "pack2")


def test_silence_clipping_corruption_and_names(tmp_path):
    src = tmp_path / "source"
    src.mkdir()
    tone(src / "black.wav", amplitude=0)
    tone(src / "blue.wav", amplitude=32767)
    (src / "red.wav").write_bytes(b"not audio")
    (src / "other.wav").write_bytes(b"")
    report = voice_pack.prepare(src, tmp_path / "staging")
    assert "silence_or_very_low_level" in report["assets"]["black"]["issues"]
    assert "clipping" in report["assets"]["blue"]["issues"]
    assert report["assets"]["red"]["issues"]
    assert report["unexpected_files"] == ["other.wav"]


def test_build_verifier_rejects_unapproved_or_modified_audio(tmp_path):
    import subprocess

    root = Path(__file__).resolve().parents[2]
    manifest = tmp_path / "src/features/recognition/domain/approved-voice-pack.json"
    manifest.parent.mkdir(parents=True)
    audio = tmp_path / "public/audio/darija/colors"
    audio.mkdir(parents=True)
    manifest.write_text(json.dumps({"version": "1", "assets": {}}))
    tone(audio / "red.wav", rate=24000)
    script = root / "apps/web/scripts/verify-darija-pack.mjs"

    def verify():
        return subprocess.run(
            ["node", str(script)], cwd=tmp_path, capture_output=True
        ).returncode

    assert verify() != 0
    digest = voice_pack.inspect(audio / "red.wav")["sha256"]
    manifest.write_text(
        json.dumps(
            {
                "version": "1",
                "assets": {
                    "red": {
                        "approved": True,
                        "sha256": digest,
                        "version": "1",
                        "expression": "حمر",
                    }
                },
            }
        )
    )
    assert verify() == 0
    (audio / "red.wav").write_bytes(b"tampered")
    assert verify() != 0
