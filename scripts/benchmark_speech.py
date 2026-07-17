import json
import statistics
import time
import urllib.error
import urllib.request


BASE_URL = "http://localhost:8081"
ANON = "speech-benchmark-session"


def request(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "X-Anonymous-Session-Id": ANON},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def prepare_message() -> str:
    created = request("/api/v1/messages", "POST", {"anonymous_session_id": ANON, "title": "Speech benchmark"})
    message_id = str(created["id"])
    request(f"/api/v1/messages/{message_id}", "PATCH", {"final_darija_arabic": "بغيت الما"})
    request(f"/api/v1/messages/{message_id}/finalize", "POST", {})
    return message_id


def main() -> None:
    message_id = prepare_message()
    latencies: list[float] = []
    for _ in range(20):
        started = time.perf_counter()
        request(
            f"/api/v1/messages/{message_id}/speech",
            "POST",
            {"voice_id": "darija-default", "speed": 1.0, "format": "wav"},
        )
        latencies.append((time.perf_counter() - started) * 1000)
    print(
        json.dumps(
            {
                "count": len(latencies),
                "mean_ms": round(statistics.mean(latencies), 2),
                "median_ms": round(statistics.median(latencies), 2),
                "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 2),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        raise SystemExit(f"Speech benchmark requires Docker/Nginx at {BASE_URL}: {exc}") from exc
