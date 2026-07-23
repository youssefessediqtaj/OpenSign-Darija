import logging

import httpx

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.recognition import (
    PredictionResponse,
    RecognitionResponse,
    WordLandmarkRecognitionRequest,
)

logger = logging.getLogger(__name__)


async def predict_sequence(payload: WordLandmarkRecognitionRequest) -> RecognitionResponse:
    settings = get_settings()
    url = f"{settings.inference_service_url.rstrip('/')}/predict/word"
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
            if not isinstance(data, dict):
                raise TypeError("inference response must be an object")
            if data.get("inference_mode") != "real":
                raise ValueError("inference response is not from the real runtime")
            if data.get("feature_schema_version") != payload.feature_schema_version:
                raise ValueError("inference response schema does not match the request")
            if data.get("sequence_id") != str(payload.sequence_id):
                raise ValueError("inference response sequence does not match the request")
            model = data["model"]
            if not isinstance(model, dict):
                raise TypeError("inference model metadata must be an object")
            return RecognitionResponse(
                request_id=data["request_id"],
                sequence_id=data["sequence_id"],
                status=data["status"],
                model_name=model["name"],
                model_version=model["version"],
                feature_schema_version=data["feature_schema_version"],
                inference_mode=data["inference_mode"],
                decision=data["decision"],
                confidence_level=data["confidence_level"],
                predictions=[PredictionResponse(**item) for item in data["predictions"]],
                unknown_probability=data["unknown_probability"],
                processing_time_ms=data["processing_time_ms"],
            )
    except ApiError:
        raise
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        logger.warning(
            "landmark inference call failed",
            extra={"error": exc.__class__.__name__, "sequence_id": str(payload.sequence_id)},
        )
        raise ApiError(
            "INFERENCE_UNAVAILABLE",
            "Le moteur de reconnaissance est temporairement indisponible.",
            503,
        ) from exc
