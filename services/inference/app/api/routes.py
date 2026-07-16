from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.prediction import PredictionResponse, PredictMockRequest
from app.services.prediction_service import PredictionService

router = APIRouter()
prediction_service = PredictionService()


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "healthy", "service": "opensign-inference", "version": settings.app_version}


@router.get("/version")
def version() -> dict[str, str]:
    settings = get_settings()
    return {"service": "opensign-inference", "version": settings.app_version}


@router.get("/model")
def model() -> dict[str, str | bool]:
    settings = get_settings()
    return {"name": settings.model_name, "version": settings.model_version, "mock": True}


@router.post("/predict/mock", response_model=PredictionResponse)
def predict_mock(payload: PredictMockRequest) -> PredictionResponse:
    return prediction_service.predict_mock(payload.frames_count)
