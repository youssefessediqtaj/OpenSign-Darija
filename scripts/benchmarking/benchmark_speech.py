from __future__ import annotations

import argparse
import base64
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_SIGNS = ROOT / "artifacts/models/mosl-isolated-sign-v1/supported-signs.json"
OUTPUT_REPORT = ROOT / "artifacts/reports/speech-runtime-benchmark.json"


def supported_label(path: Path) -> tuple[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    signs = payload.get("signs", [])
    if not signs:
        raise RuntimeError("The selected model package has no supported signs")
    return str(signs[0]["label_key"]), str(signs[0]["label_ar"])


def percentile_95(values: list[float]) -> float:
    return sorted(values)[max(0, int(len(values) * 0.95) - 1)]


def request_speech(url: str, label_key: str) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        url,
        data=json.dumps({"label_key": label_key}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=30) as response:
        result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    return result, (time.perf_counter() - started) * 1000


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark direct offline sign speech.")
    parser.add_argument(
        "--url", default="http://localhost:8081/api/v1/speech/sign"
    )
    parser.add_argument("--requests", type=int, default=5)
    parser.add_argument("--supported-signs", type=Path, default=SUPPORTED_SIGNS)
    parser.add_argument("--output", type=Path, default=OUTPUT_REPORT)
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 20:
        raise SystemExit("--requests must be between 1 and 20")

    label_key, expected_ar = supported_label(args.supported_signs)
    latencies: list[float] = []
    audio_sizes: list[int] = []
    durations: list[int] = []
    fallback_count = 0
    try:
        for _ in range(args.requests):
            result, latency = request_speech(args.url, label_key)
            if result.get("status") != "completed" or result.get("label_ar") != expected_ar:
                raise RuntimeError(f"Unexpected speech response: {result}")
            audio = result.get("audio")
            if not isinstance(audio, dict) or not str(audio.get("url", "")).startswith(
                "data:audio/wav;base64,"
            ):
                raise RuntimeError("Speech response did not contain playable WAV data")
            encoded = str(audio["url"]).split(",", 1)[1]
            decoded = base64.b64decode(encoded, validate=True)
            if not decoded.startswith(b"RIFF") or b"WAVE" not in decoded[:16]:
                raise RuntimeError("Speech payload is not a WAV file")
            latencies.append(latency)
            audio_sizes.append(len(decoded))
            durations.append(int(audio.get("duration_ms", 0)))
            fallback_count += int(bool(result.get("fallback_used")))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SystemExit(f"Real Docker speech API is unavailable at {args.url}: {exc}") from exc

    report = {
        "schema_version": "OPEN_SIGNE_SPEECH_BENCHMARK_V1",
        "measured_at": datetime.now(UTC).isoformat(),
        "url": args.url,
        "requests": args.requests,
        "label_key": label_key,
        "label_ar": expected_ar,
        "generation_latency_ms": {
            "average": round(statistics.mean(latencies), 3),
            "p50": round(statistics.median(latencies), 3),
            "p95": round(percentile_95(latencies), 3),
            "maximum": round(max(latencies), 3),
        },
        "average_audio_bytes": round(statistics.mean(audio_sizes), 1),
        "average_audio_duration_ms": round(statistics.mean(durations), 1),
        "fallback_count": fallback_count,
        "playable_wav_count": len(audio_sizes),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
