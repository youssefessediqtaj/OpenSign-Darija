import logging
from uuid import uuid4

import httpx

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.recognition import (
    LandmarkRecognitionRequest,
    PredictionResponse,
    RecognitionResponse,
)

logger = logging.getLogger(__name__)


def fallback_prediction() -> RecognitionResponse:
    return RecognitionResponse(
        request_id=str(uuid4()),
        status="completed",
        model_name="opensign-darija-mock-fallback",
        model_version="0.1.0",
        inference_mode="mock",
        decision="known",
        confidence_level="high",
        predictions=[
            PredictionResponse(label="aide", confidence=0.78, rank=1),
            PredictionResponse(label="merci", confidence=0.14, rank=2),
            PredictionResponse(label="oui", confidence=0.05, rank=3),
        ],
        unknown_probability=0.03,
        processing_time_ms=1,
    )


async def predict_mock(frames_count: int) -> RecognitionResponse:
    settings = get_settings()
    url = f"{settings.inference_service_url.rstrip('/')}/predict/mock"
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=settings.inference_timeout_seconds) as client:
                response = await client.post(url, json={"frames_count": frames_count})
                response.raise_for_status()
                data = response.json()
                return RecognitionResponse(
                    request_id=data["request_id"],
                    status=data["status"],
                    model_name=data["model"]["name"],
                    model_version=data["model"]["version"],
                    feature_schema_version=data.get("feature_schema_version"),
                    inference_mode=data.get("inference_mode", "mock"),
                    decision=data.get("decision", "known"),
                    confidence_level=data.get("confidence_level", "high"),
                    predictions=[PredictionResponse(**item) for item in data["predictions"]],
                    unknown_probability=data["unknown_probability"],
                    processing_time_ms=data["processing_time_ms"],
                )
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            logger.warning(
                "mock inference call failed",
                extra={"attempt": attempt + 1, "error": exc.__class__.__name__},
            )
    return fallback_prediction()


async def predict_sequence(payload: LandmarkRecognitionRequest) -> RecognitionResponse:
    settings = get_settings()
    url = f"{settings.inference_service_url.rstrip('/')}/predict"
    try:
        async with httpx.AsyncClient(timeout=settings.inference_timeout_seconds) as client:
            response = await client.post(url, json=payload.model_dump(mode="json"))
            if response.status_code == 422:
                raise ApiError(
                    "FEATURE_SCHEMA_MISMATCH",
                    "Le format des mouvements n’est pas compatible avec le modèle actif.",
                    422,
                    {"feature_schema_version": payload.feature_schema_version},
                )
            if response.status_code in {404, 409, 503}:
                raise ApiError(
                    "INFERENCE_MODEL_UNAVAILABLE",
                    "Le moteur de reconnaissance est temporairement indisponible.",
                    503,
                )
            response.raise_for_status()
            data = response.json()
            return RecognitionResponse(
                request_id=data["request_id"],
                sequence_id=data.get("sequence_id"),
                status=data["status"],
                model_name=data["model"]["name"],
                model_version=data["model"]["version"],
                feature_schema_version=data.get("feature_schema_version"),
                inference_mode=data.get("inference_mode", "real"),
                decision=data.get("decision", "known"),
                confidence_level=data.get("confidence_level", "high"),
                predictions=[PredictionResponse(**item) for item in data["predictions"]],
                unknown_probability=data["unknown_probability"],
                processing_time_ms=data["processing_time_ms"],
            )
    except ApiError:
        raise
    except (httpx.HTTPError, KeyError, TypeError) as exc:
        logger.warning(
            "landmark inference call failed",
            extra={"error": exc.__class__.__name__, "sequence_id": str(payload.sequence_id)},
        )
        if settings.inference_mode == "mock" and settings.app_env != "production":
            fallback = fallback_prediction()
            fallback.sequence_id = str(payload.sequence_id)
            fallback.feature_schema_version = payload.feature_schema_version
            fallback.model_name = "opensign-darija-landmark-mock-fallback"
            fallback.model_version = "0.2.0"
            return fallback
        raise ApiError(
            "INFERENCE_UNAVAILABLE",
            "Le moteur de reconnaissance est temporairement indisponible.",
            503,
        ) from exc
