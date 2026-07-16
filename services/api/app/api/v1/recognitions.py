from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import RecognitionStatus
from app.models.recognition import RecognitionPrediction, RecognitionSession
from app.schemas.recognition import RecognitionMockRequest, RecognitionResponse
from app.services.inference_client import predict_mock

router = APIRouter(prefix="/recognitions", tags=["recognitions"])


@router.post("/mock", response_model=RecognitionResponse)
async def mock_recognition(
    payload: RecognitionMockRequest, db: Annotated[Session, Depends(get_db)]
) -> RecognitionResponse:
    result = await predict_mock(payload.frames_count)
    session = RecognitionSession(status=RecognitionStatus.COMPLETED)
    db.add(session)
    db.flush()
    for prediction in result.predictions:
        db.add(
            RecognitionPrediction(
                recognition_session_id=session.id,
                predicted_label=prediction.label,
                confidence=prediction.confidence,
                rank=prediction.rank,
                model_version=result.model_version,
            )
        )
    db.commit()
    return result
