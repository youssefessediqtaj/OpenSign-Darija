from time import perf_counter

from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.schemas.recognition import PublicRecognitionResponse, WordLandmarkRecognitionRequest
from app.services.recognition import recognize_isolated_sign
from app.services.request_protection import enforce_recognition_request_limits

router = APIRouter(prefix="/recognitions", tags=["recognitions"])


@router.post("/word", response_model=PublicRecognitionResponse)
async def create_word_recognition(
    payload: WordLandmarkRecognitionRequest,
    request: Request,
) -> PublicRecognitionResponse:
    if get_settings().colors_experimental_enabled:
        raise HTTPException(status_code=404, detail="Legacy recognition disabled")
    started = perf_counter()
    enforce_recognition_request_limits(request)
    return await recognize_isolated_sign(payload, started)
