#!/usr/bin/env python3
"""Prepare private candidates or package separately approved, hash-bound WAVs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

WORDS = {
    "black": "كحل",
    "blue": "زرق",
    "brown": "قهوي",
    "green": "خضر",
    "orange": "ليموني",
    "pink": "وردي",
    "red": "حمر",
    "white": "بيض",
    "yellow": "صفر",
}
LABELS = tuple(WORDS)


def inspect(path: Path) -> dict:
    with wave.open(str(path), "rb") as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) != (
            1,
            2,
            24000,
            "NONE",
        ):
            raise ValueError("expected mono PCM16 at 24000 Hz")
        n = w.getnframes()
        data = w.readframes(n)
        if len(data) != n * 2:
            raise ValueError("truncated WAV")
    samples = [v[0] for v in struct.iter_unpack("<h", data)]
    duration = n / 24000
    peak = max((abs(x) for x in samples), default=0)
    rms = math.sqrt(sum(x * x for x in samples) / n) if n else 0
    problems = []
    if not 0.15 <= duration <= 5:
        problems.append("abnormal_duration")
    if rms < 100:
        problems.append("silence_or_very_low_level")
    if peak >= 32700:
        problems.append("clipping")
    return {
        "duration_seconds": round(duration, 3),
        "peak": peak,
        "rms": round(rms, 1),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "issues": problems,
    }


def convert(source: Path, destination: Path) -> None:
    result = subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "24000",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise ValueError("audio decode/conversion failed")


def trim_silence(path: Path) -> None:
    # A conservative amplitude gate with 50 ms padding; human listening remains required.
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
    samples = [v[0] for v in struct.iter_unpack("<h", data)]
    active = [i for i, sample in enumerate(samples) if abs(sample) >= 200]
    if not active:
        return
    start = max(0, active[0] - 1200)
    end = min(len(samples), active[-1] + 1201)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(data[start * 2 : end * 2])


def prepare(source: Path, staging: Path) -> dict:
    if not source.is_dir():
        raise ValueError("source directory does not exist")
    staging.mkdir(parents=True, exist_ok=False)
    results = {}
    unexpected = sorted(
        p.name
        for p in source.iterdir()
        if p.is_file() and p.name not in {f"{x}.wav" for x in LABELS}
    )
    for label in LABELS:
        src, dst = source / f"{label}.wav", staging / f"{label}.wav"
        if not src.is_file() or src.is_symlink():
            results[label] = {"issues": ["missing_or_symlink"]}
            continue
        try:
            convert(src, dst)
            before = inspect(dst)
            trim_silence(dst)
            results[label] = inspect(dst)
            if (
                "clipping" in before["issues"]
                and "clipping" not in results[label]["issues"]
            ):
                results[label]["issues"].append("clipping")
        except (OSError, ValueError, wave.Error, subprocess.TimeoutExpired) as exc:
            dst.unlink(missing_ok=True)
            results[label] = {"issues": [str(exc)]}
    report = {
        "schema": 1,
        "technical_checks_only": True,
        "unexpected_files": unexpected,
        "assets": results,
    }
    (staging / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def package(staging: Path, approvals_path: Path, output: Path) -> dict:
    approvals = json.loads(approvals_path.read_text())
    if not isinstance(approvals, dict) or not isinstance(approvals.get("assets"), dict):
        raise ValueError("invalid approval record")
    entries = approvals["assets"]
    if not entries or not set(entries).issubset(LABELS):
        raise ValueError("invalid or empty labels in approval record")
    selected = {}
    for label, approval in entries.items():
        if not isinstance(approval, dict):
            raise ValueError(f"{label}: invalid approval")
        path = staging / f"{label}.wav"
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"{label}: missing candidate")
        info = inspect(path)
        if info["issues"]:
            raise ValueError(f"{label}: technical checks failed")
        for field in ("version", "review_reference", "rights_reference"):
            if not isinstance(approval.get(field), str) or not approval[field].strip():
                raise ValueError(f"{label}: {field} required")
        if (
            approval.get("text_approved") is not True
            or approval.get("audio_approved") is not True
            or approval.get("rights_approved") is not True
        ):
            raise ValueError(
                f"{label}: explicit text, audio and rights approval required"
            )
        if approval.get("expression") != WORDS[label]:
            raise ValueError(f"{label}: expression does not match vocabulary")
        if approval.get("sha256") != info["sha256"]:
            raise ValueError(f"{label}: checksum does not match reviewed recording")
        selected[label] = {
            "approved": True,
            "sha256": info["sha256"],
            "version": approval["version"],
            "expression": WORDS[label],
        }
    output.mkdir(parents=True, exist_ok=False)
    for label in selected:
        shutil.copyfile(staging / f"{label}.wav", output / f"{label}.wav")
    manifest = {"version": "1", "assets": selected}
    (output / "approved-voice-pack.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--source", type=Path, required=True)
    prep.add_argument("--staging", type=Path, required=True)
    pack = sub.add_parser("package")
    pack.add_argument("--staging", type=Path, required=True)
    pack.add_argument("--approvals", type=Path, required=True)
    pack.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            prepare(args.source, args.staging)
            if args.command == "prepare"
            else package(args.staging, args.approvals, args.output)
        )
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, wave.Error, json.JSONDecodeError) as exc:
        print(f"voice pack error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
