from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.enums import RecognitionStatus
from app.models.recognition import RecognitionPrediction, RecognitionSession
from app.models.sign import Sign
from app.models.user import User
from app.schemas.recognition import (
    ConfirmRecognitionRequest,
    CorrectRecognitionRequest,
    LandmarkRecognitionRequest,
    PredictionResponse,
    RecognitionMockRequest,
    RecognitionResponse,
)
from app.services.inference_client import predict_mock, predict_sequence

from .signs import sign_to_response

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


def rate_limit_key(
    current_user: User | None, payload: LandmarkRecognitionRequest, request: Request
) -> str:
    if current_user:
        return current_user.id
    if payload.anonymous_session_id:
        return payload.anonymous_session_id
    if request.client:
        return request.client.host
    return "guest"


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


def enrich_and_store_predictions(
    db: Session, session: RecognitionSession, result: RecognitionResponse
) -> list[PredictionResponse]:
    signs = db.scalars(select(Sign).options(selectinload(Sign.category))).all()
    by_slug = {sign.slug: sign for sign in signs}
    by_meaning = {sign.canonical_meaning: sign for sign in signs}
    enriched: list[PredictionResponse] = []
    for prediction in result.predictions:
        sign = by_slug.get(prediction.label) or by_meaning.get(prediction.label)
        stored = RecognitionPrediction(
            recognition_session_id=session.id,
            sign_id=sign.id if sign else None,
            predicted_label=prediction.label,
            confidence=prediction.confidence,
            rank=prediction.rank,
            model_version=result.model_version,
        )
        db.add(stored)
        db.flush()
        enriched.append(
            PredictionResponse(
                prediction_id=stored.id,
                label=prediction.label,
                confidence=prediction.confidence,
                rank=prediction.rank,
                sign=sign_to_response(sign) if sign else None,
            )
        )
    return enriched


@router.post("/mock", response_model=RecognitionResponse)
async def mock_recognition(
    payload: RecognitionMockRequest, db: Annotated[Session, Depends(get_db)]
) -> RecognitionResponse:
    result = await predict_mock(payload.frames_count)
    session = RecognitionSession(status=RecognitionStatus.COMPLETED)
    db.add(session)
    db.flush()
    result.predictions = enrich_and_store_predictions(db, session, result)
    db.commit()
    return result


@router.post("", response_model=RecognitionResponse)
async def create_recognition(
    payload: LandmarkRecognitionRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> RecognitionResponse:
    assert_payload_size(request)
    check_rate_limit(rate_limit_key(current_user, payload, request))
    result = await predict_sequence(payload)
    session = RecognitionSession(
        user_id=current_user.id if current_user else None,
        status=RecognitionStatus.COMPLETED,
        completed_at=datetime.now(UTC),
    )
    db.add(session)
    db.flush()
    result.recognition_id = session.id
    result.predictions = enrich_and_store_predictions(db, session, result)
    db.commit()
    return result


@router.post("/{recognition_id}/confirm")
def confirm_recognition(
    recognition_id: str,
    payload: ConfirmRecognitionRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    prediction = db.scalar(
        select(RecognitionPrediction).where(
            RecognitionPrediction.id == str(payload.prediction_id),
            RecognitionPrediction.recognition_session_id == recognition_id,
        )
    )
    if prediction is None:
        raise ApiError("NOT_FOUND", "Prediction introuvable.", 404)
    return {"status": "confirmed", "recognition_id": recognition_id, "prediction_id": prediction.id}


@router.post("/{recognition_id}/correct")
def correct_recognition(
    recognition_id: str,
    payload: CorrectRecognitionRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str | None]:
    session = db.scalar(select(RecognitionSession).where(RecognitionSession.id == recognition_id))
    if session is None:
        raise ApiError("NOT_FOUND", "Session de reconnaissance introuvable.", 404)
    if payload.correct_sign_id is not None:
        sign = db.scalar(select(Sign).where(Sign.id == str(payload.correct_sign_id)))
        if sign is None:
            raise ApiError("NOT_FOUND", "Signe de correction introuvable.", 404)
    return {
        "status": "correction_received",
        "recognition_id": recognition_id,
        "correct_sign_id": str(payload.correct_sign_id) if payload.correct_sign_id else None,
        "reason": payload.reason,
    }
