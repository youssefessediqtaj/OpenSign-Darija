from fastapi import APIRouter

from app.schemas.speech import SignSpeechRequest, SignSpeechResponse
from app.services.sign_speech import synthesize_supported_sign

router = APIRouter(tags=["speech"])


@router.post("/speech/sign", response_model=SignSpeechResponse)
def create_sign_speech(payload: SignSpeechRequest) -> SignSpeechResponse:
    return synthesize_supported_sign(payload)
