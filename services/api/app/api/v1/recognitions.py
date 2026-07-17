from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.enums import ConfidenceLevel, CorrectionType, RecognitionDecision, RecognitionStatus
from app.models.recognition import RecognitionPrediction, RecognitionSession, UserCorrection
from app.models.sign import ModelVersion, Sign
from app.models.user import User
from app.schemas.recognition import (
    ActiveModelResponse,
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
            is_unknown=result.decision == "unknown",
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
                is_unknown=result.decision == "unknown",
            )
        )
    return enriched


def quality_score(payload: LandmarkRecognitionRequest) -> float:
    return round(
        (
            payload.quality.detected_hand_ratio * 0.45
            + payload.quality.detected_pose_ratio * 0.2
            + payload.quality.detected_face_ratio * 0.1
            + payload.quality.movement_score * 0.2
            + (1 - payload.quality.missing_frame_ratio) * 0.05
        ),
        4,
    )


@router.post("/mock", response_model=RecognitionResponse)
async def mock_recognition(
    payload: RecognitionMockRequest, db: Annotated[Session, Depends(get_db)]
) -> RecognitionResponse:
    result = await predict_mock(payload.frames_count)
    session = RecognitionSession(
        status=RecognitionStatus.COMPLETED,
        inference_mode=result.inference_mode,
        model_name=result.model_name,
        model_version=result.model_version,
        feature_schema_version=result.feature_schema_version
        or get_settings().feature_schema_version,
        decision=RecognitionDecision(result.decision),
        confidence_level=ConfidenceLevel(result.confidence_level),
        processing_time_ms=result.processing_time_ms,
    )
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
        feature_schema_version=result.feature_schema_version or payload.feature_schema_version,
        inference_mode=result.inference_mode,
        model_name=result.model_name,
        model_version=result.model_version,
        decision=RecognitionDecision(result.decision),
        confidence_level=ConfidenceLevel(result.confidence_level),
        processing_time_ms=result.processing_time_ms,
        quality_score=quality_score(payload),
    )
    db.add(session)
    db.flush()
    result.recognition_id = session.id
    result.predictions = enrich_and_store_predictions(db, session, result)
    db.commit()
    return result


@router.get("/{recognition_id}", response_model=RecognitionResponse)
def get_recognition(
    recognition_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> RecognitionResponse:
    session = db.scalar(
        select(RecognitionSession)
        .options(selectinload(RecognitionSession.predictions))
        .where(RecognitionSession.id == recognition_id)
    )
    if session is None:
        raise ApiError("NOT_FOUND", "Session de reconnaissance introuvable.", 404)
    if session.user_id and (current_user is None or current_user.id != session.user_id):
        raise ApiError("FORBIDDEN", "Acces refuse a cette session.", 403)
    predictions = []
    for prediction in sorted(session.predictions, key=lambda item: item.rank):
        sign = (
            db.scalar(
                select(Sign)
                .options(selectinload(Sign.category))
                .where(Sign.id == prediction.sign_id)
            )
            if prediction.sign_id
            else None
        )
        predictions.append(
            PredictionResponse(
                prediction_id=prediction.id,
                label=prediction.predicted_label,
                confidence=prediction.confidence,
                rank=prediction.rank,
                sign=sign_to_response(sign) if sign else None,
                is_unknown=prediction.is_unknown,
            )
        )
    return RecognitionResponse(
        recognition_id=session.id,
        request_id=session.id,
        status=session.status.value.lower(),
        model_name=session.model_name,
        model_version=session.model_version,
        feature_schema_version=session.feature_schema_version,
        inference_mode=session.inference_mode,
        decision=session.decision.value if session.decision else "known",
        confidence_level=session.confidence_level.value if session.confidence_level else "high",
        predictions=predictions,
        unknown_probability=max(0.0, 1.0 - predictions[0].confidence) if predictions else 1.0,
        processing_time_ms=session.processing_time_ms,
    )


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
    correction_type = (
        CorrectionType.CONFIRMED_TOP_1
        if prediction.rank == 1
        else CorrectionType.SELECTED_ALTERNATIVE
    )
    db.add(
        UserCorrection(
            recognition_session_id=recognition_id,
            selected_sign_id=prediction.sign_id,
            correction_type=correction_type,
        )
    )
    db.commit()
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
    db.add(
        UserCorrection(
            recognition_session_id=recognition_id,
            selected_sign_id=str(payload.correct_sign_id) if payload.correct_sign_id else None,
            correction_type=(
                CorrectionType.SELECTED_OTHER_SIGN
                if payload.correct_sign_id
                else CorrectionType.MARKED_UNKNOWN
            ),
            comment=payload.comment or payload.reason,
        )
    )
    db.commit()
    return {
        "status": "correction_received",
        "recognition_id": recognition_id,
        "correct_sign_id": str(payload.correct_sign_id) if payload.correct_sign_id else None,
        "reason": payload.reason,
    }


models_router = APIRouter(prefix="/models", tags=["models"])


@models_router.get("/active", response_model=ActiveModelResponse)
def active_model(db: Annotated[Session, Depends(get_db)]) -> ActiveModelResponse:
    model = db.scalar(select(ModelVersion).where(ModelVersion.is_active.is_(True)))
    if model is None:
        return ActiveModelResponse(
            id=None,
            name="opensign-darija-landmark-mock",
            semantic_version="0.2.0",
            status="MOCK_ONLY",
            architecture="mock",
            vocabulary_size=10,
            feature_schema_version=get_settings().feature_schema_version,
            metrics_json={},
            thresholds_json={"unknown_threshold": 0.6},
            is_active=False,
        )
    return ActiveModelResponse(
        id=model.id,
        name=model.name,
        semantic_version=model.semantic_version,
        status=model.status.value,
        architecture=model.architecture,
        vocabulary_size=model.vocabulary_size,
        feature_schema_version=model.feature_schema_version,
        metrics_json=model.metrics_json,
        thresholds_json=model.thresholds_json,
        is_active=model.is_active,
    )
