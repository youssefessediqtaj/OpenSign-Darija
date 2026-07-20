from datetime import UTC, datetime
from time import perf_counter

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.recognition import PublicRecognitionResponse, WordLandmarkRecognitionRequest
from app.services.inference_client import predict_sequence

router = APIRouter(prefix="/recognitions", tags=["recognitions"])
rate_limit_bucket: dict[str, list[float]] = {}


def check_rate_limit(key: str) -> None:
    settings = get_settings()
    now = datetime.now(UTC).timestamp()
    window_start = now - 60
    entries = [entry for entry in rate_limit_bucket.get(key, []) if entry > window_start]
    if len(entries) >= settings.recognition_rate_limit:
        raise ApiError("RATE_LIMITED", "Trop de reconnaissances en peu de temps.", 429)
    entries.append(now)
    rate_limit_bucket[key] = entries


def rate_limit_key(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown-client"


def assert_payload_size(request: Request) -> None:
    max_bytes = get_settings().recognition_max_payload_bytes
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_bytes:
        raise ApiError(
            "PAYLOAD_TOO_LARGE",
            "La sequence de mouvements est trop volumineuse.",
            413,
            {"max_bytes": max_bytes},
        )


def word_quality_rejection(payload: WordLandmarkRecognitionRequest) -> str | None:
    settings = get_settings()
    if not settings.recognition_min_duration_ms <= payload.duration_ms <= (
        settings.recognition_max_duration_ms
    ):
        return "invalid_duration"
    if not payload.segmentation_reliable:
        return "unreliable_segmentation"
    if payload.quality.detected_hand_ratio < settings.recognition_min_hand_ratio:
        return "insufficient_hand_visibility"
    if payload.quality.missing_frame_ratio > settings.recognition_max_missing_frame_ratio:
        return "excessive_missing_frames"
    if payload.quality.detected_pose_ratio < 0.2:
        return "insufficient_pose_visibility"
    visible_hand_frames = sum(any(frame.presence_mask[33:]) for frame in payload.frames)
    usable_frames = min(payload.usable_frame_count, visible_hand_frames)
    if usable_frames < settings.recognition_min_usable_frames:
        return "insufficient_usable_frames"
    if (
        payload.segmentation_kind == "dynamic"
        and payload.quality.movement_score < settings.recognition_min_dynamic_movement
    ):
        return "insufficient_dynamic_movement"
    return None


def public_unknown(started: float, confidence: float = 0.0) -> PublicRecognitionResponse:
    return PublicRecognitionResponse(
        status="unknown",
        label_key=None,
        label_ar=None,
        confidence=round(max(0.0, min(1.0, confidence)), 4),
        unknown=True,
        latency_ms=max(0, round((perf_counter() - started) * 1000)),
    )


@router.post("/word", response_model=PublicRecognitionResponse)
async def create_word_recognition(
    payload: WordLandmarkRecognitionRequest,
    request: Request,
) -> PublicRecognitionResponse:
    started = perf_counter()
    assert_payload_size(request)
    check_rate_limit(rate_limit_key(request))
    if word_quality_rejection(payload) is not None:
        return public_unknown(started)
    result = await predict_sequence(payload)
    top = min(result.predictions, key=lambda item: item.rank) if result.predictions else None
    confidence = top.confidence if top else max(0.0, 1.0 - result.unknown_probability)
    if result.decision != "known" or top is None or not top.label_ar:
        return public_unknown(started, confidence)
    return PublicRecognitionResponse(
        status="recognized",
        label_key=top.label,
        label_ar=top.label_ar,
        confidence=round(top.confidence, 4),
        unknown=False,
        latency_ms=max(0, round((perf_counter() - started) * 1000)),
    )
