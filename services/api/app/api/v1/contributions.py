from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import (
    AuditLog,
    CampaignSign,
    ConsentRecord,
    ContributionRecording,
    ContributorProfile,
    DatasetContribution,
    RecordingQualityMetric,
)
from app.models.enums import (
    AutomaticQualityStatus,
    CampaignStatus,
    ConsentType,
    ContributionStatus,
    UserRoleName,
)
from app.models.sign import Sign
from app.models.user import User
from app.schemas.dataset import (
    ConfirmUploadRequest,
    ContributionCreateRequest,
    ContributionResponse,
    ContributionUpdateRequest,
    RecordingCreateRequest,
    RecordingResponse,
    UploadSessionRequest,
    UploadSessionResponse,
    UploadTarget,
)
from app.services.object_storage import (
    PRIVATE_LANDMARK_BUCKET,
    PRIVATE_VIDEO_BUCKET,
    ObjectStorage,
    recording_object_prefix,
)

router = APIRouter(prefix="/contributions", tags=["contributions"])

REQUIRED_LANDMARK_CONSENTS = {
    ConsentType.LANDMARK_PROCESSING,
    ConsentType.LANDMARK_STORAGE,
    ConsentType.RESEARCH_USE,
    ConsentType.MODEL_TRAINING,
}
VIDEO_CONSENTS = {ConsentType.VIDEO_RECORDING, ConsentType.VIDEO_STORAGE}


def get_profile(db: Session, user: User) -> ContributorProfile:
    profile = db.scalar(select(ContributorProfile).where(ContributorProfile.user_id == user.id))
    if profile is None:
        raise ApiError("CONTRIBUTOR_PROFILE_REQUIRED", "Profil contributeur requis.", 403)
    return profile


def active_consents(db: Session, user_id: str) -> dict[str, bool]:
    records = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id)
        .order_by(ConsentRecord.created_at.asc())
    )
    active: dict[str, bool] = {}
    for record in records:
        active[record.consent_type.value] = record.granted and record.revoked_at is None
    return active


def assert_required_consents(consents: dict[str, bool], wants_video: bool) -> None:
    missing = [
        consent.value for consent in REQUIRED_LANDMARK_CONSENTS if not consents.get(consent.value)
    ]
    if wants_video:
        missing.extend(
            [consent.value for consent in VIDEO_CONSENTS if not consents.get(consent.value)]
        )
    if missing:
        raise ApiError(
            "CONSENT_REQUIRED",
            "Consentements requis manquants.",
            403,
            {"missing": sorted(set(missing))},
        )


def contribution_query() -> Select[tuple[DatasetContribution]]:
    return select(DatasetContribution).options(
        selectinload(DatasetContribution.campaign),
        selectinload(DatasetContribution.campaign_sign)
        .selectinload(CampaignSign.sign)
        .selectinload(Sign.category),
        selectinload(DatasetContribution.recordings).selectinload(ContributionRecording.metrics),
    )


def owned_contribution(db: Session, user: User, contribution_id: str) -> DatasetContribution:
    profile = get_profile(db, user)
    contribution: DatasetContribution | None = db.scalar(
        contribution_query().where(
            DatasetContribution.id == contribution_id,
            DatasetContribution.contributor_id == profile.id,
        )
    )
    if contribution is None:
        raise ApiError("NOT_FOUND", "Contribution introuvable.", 404)
    return contribution


@router.post("", response_model=ContributionResponse, status_code=201)
def create_contribution(
    payload: ContributionCreateRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    profile = get_profile(db, current_user)
    campaign_sign = db.scalar(
        select(CampaignSign)
        .options(
            selectinload(CampaignSign.campaign),
            selectinload(CampaignSign.sign).selectinload(Sign.category),
        )
        .where(
            CampaignSign.id == payload.campaign_sign_id,
            CampaignSign.campaign_id == payload.campaign_id,
            CampaignSign.is_active.is_(True),
        )
    )
    if campaign_sign is None:
        raise ApiError("CAMPAIGN_SIGN_NOT_FOUND", "Signe absent de cette campagne.", 404)
    if campaign_sign.campaign.status != CampaignStatus.ACTIVE:
        raise ApiError("CAMPAIGN_INACTIVE", "La campagne n'est pas active.", 409)
    consents = active_consents(db, current_user.id)
    assert_required_consents(consents, payload.wants_video)
    contribution = DatasetContribution(
        contributor_id=profile.id,
        campaign_id=payload.campaign_id,
        campaign_sign_id=payload.campaign_sign_id,
        status=ContributionStatus.DRAFT,
        consent_snapshot={
            "consents": consents,
            "wants_video": payload.wants_video,
            "captured_at": datetime.now(UTC).isoformat(),
        },
    )
    db.add(contribution)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="CONTRIBUTION_CREATED",
            target_type="DatasetContribution",
            target_id=contribution.id,
            details={
                "campaign_id": payload.campaign_id,
                "campaign_sign_id": payload.campaign_sign_id,
            },
        )
    )
    db.commit()
    return owned_contribution(db, current_user, contribution.id)


@router.get("/me", response_model=list[ContributionResponse])
def my_contributions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[DatasetContribution]:
    profile = get_profile(db, current_user)
    return list(
        db.scalars(
            contribution_query()
            .where(DatasetContribution.contributor_id == profile.id)
            .order_by(DatasetContribution.created_at.desc())
        )
    )


@router.get("/{contribution_id}", response_model=ContributionResponse)
def get_contribution(
    contribution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    return owned_contribution(db, current_user, contribution_id)


@router.patch("/{contribution_id}", response_model=ContributionResponse)
def update_contribution(
    contribution_id: str,
    payload: ContributionUpdateRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    contribution = owned_contribution(db, current_user, contribution_id)
    if payload.status is not None:
        allowed = {
            ContributionStatus.DRAFT: {
                ContributionStatus.CAPTURING,
                ContributionStatus.READY_TO_SUBMIT,
            },
            ContributionStatus.CAPTURING: {
                ContributionStatus.READY_TO_SUBMIT,
                ContributionStatus.DRAFT,
            },
            ContributionStatus.READY_TO_SUBMIT: {ContributionStatus.CAPTURING},
        }
        target = ContributionStatus(payload.status)
        if target not in allowed.get(contribution.status, set()):
            raise ApiError("INVALID_STATUS_TRANSITION", "Transition de statut interdite.", 409)
        contribution.status = target
    db.commit()
    return owned_contribution(db, current_user, contribution_id)


@router.delete("/{contribution_id}")
def delete_contribution(
    contribution_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    contribution = owned_contribution(db, current_user, contribution_id)
    if contribution.status not in {
        ContributionStatus.DRAFT,
        ContributionStatus.CAPTURING,
        ContributionStatus.READY_TO_SUBMIT,
    }:
        raise ApiError("DELETE_NOT_ALLOWED", "Cette contribution ne peut plus etre supprimee.", 409)
    db.delete(contribution)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="CONTRIBUTION_DELETED",
            target_type="DatasetContribution",
            target_id=contribution_id,
            details={},
        )
    )
    db.commit()
    return {"status": "deleted", "contribution_id": contribution_id}


@router.post("/{contribution_id}/recordings", response_model=RecordingResponse, status_code=201)
def add_recording(
    contribution_id: str,
    payload: RecordingCreateRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ContributionRecording:
    contribution = owned_contribution(db, current_user, contribution_id)
    if contribution.status not in {
        ContributionStatus.DRAFT,
        ContributionStatus.CAPTURING,
        ContributionStatus.READY_TO_SUBMIT,
    }:
        raise ApiError("INVALID_STATUS", "Impossible d'ajouter une repetition dans ce statut.", 409)
    if len(contribution.recordings) >= contribution.campaign.maximum_repetitions_per_submission:
        raise ApiError("MAX_REPETITIONS_REACHED", "Nombre maximal de repetitions atteint.", 409)
    campaign_sign = contribution.campaign_sign
    if (
        payload.duration_ms < campaign_sign.minimum_duration_ms
        or payload.duration_ms > campaign_sign.maximum_duration_ms
    ):
        raise ApiError("INVALID_DURATION", "Duree de repetition hors limites.", 422)
    if payload.feature_schema_version != get_settings().feature_schema_version:
        raise ApiError("SCHEMA_MISMATCH", "Version de schema landmarks incompatible.", 422)
    if payload.file_size_bytes > 0 and not contribution.consent_snapshot.get("wants_video"):
        raise ApiError(
            "VIDEO_CONSENT_REQUIRED", "La video n'est pas autorisee pour cette contribution.", 403
        )

    profile = contribution.contributor
    recording_id = __import__("uuid").uuid4().__str__()
    prefix = recording_object_prefix(
        contribution.campaign_id, profile.public_id, contribution.id, recording_id
    )
    quality_status = payload.automatic_quality_status
    if payload.quality_score < 0.5:
        quality_status = AutomaticQualityStatus.FAILED
    elif payload.quality_score < 0.75 and quality_status == AutomaticQualityStatus.PASSED:
        quality_status = AutomaticQualityStatus.WARNING
    recording = ContributionRecording(
        id=recording_id,
        contribution_id=contribution.id,
        repetition_index=payload.repetition_index,
        landmark_object_key=f"{prefix}/landmarks.json.gz",
        video_object_key=f"{prefix}/video.webm" if payload.file_size_bytes > 0 else None,
        feature_schema_version=payload.feature_schema_version,
        duration_ms=payload.duration_ms,
        source_fps=payload.source_fps,
        target_frame_count=payload.target_frame_count,
        video_width=payload.video_width,
        video_height=payload.video_height,
        file_size_bytes=payload.file_size_bytes,
        landmark_size_bytes=payload.landmark_size_bytes,
        checksum_video=payload.checksum_video,
        checksum_landmarks=payload.checksum_landmarks,
        quality_score=payload.quality_score,
        automatic_quality_status=quality_status,
    )
    db.add(recording)
    for metric in payload.metrics:
        db.add(RecordingQualityMetric(recording=recording, **metric.model_dump()))
    contribution.status = (
        ContributionStatus.AUTOMATIC_CHECK_FAILED
        if quality_status == AutomaticQualityStatus.FAILED
        else ContributionStatus.READY_TO_SUBMIT
    )
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="RECORDING_ADDED",
            target_type="ContributionRecording",
            target_id=recording.id,
            details={"quality_status": quality_status.value},
        )
    )
    db.commit()
    db.refresh(recording)
    return recording


@router.get("/{contribution_id}/recordings", response_model=list[RecordingResponse])
def list_recordings(
    contribution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ContributionRecording]:
    contribution = owned_contribution(db, current_user, contribution_id)
    return contribution.recordings


@router.delete("/{contribution_id}/recordings/{recording_id}")
def delete_recording(
    contribution_id: str,
    recording_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    contribution = owned_contribution(db, current_user, contribution_id)
    if contribution.status not in {
        ContributionStatus.DRAFT,
        ContributionStatus.CAPTURING,
        ContributionStatus.READY_TO_SUBMIT,
    }:
        raise ApiError("DELETE_NOT_ALLOWED", "Cette repetition ne peut plus etre supprimee.", 409)
    recording = next((item for item in contribution.recordings if item.id == recording_id), None)
    if recording is None:
        raise ApiError("NOT_FOUND", "Repetition introuvable.", 404)
    db.delete(recording)
    db.commit()
    return {"status": "deleted", "recording_id": recording_id}


@router.post(
    "/{contribution_id}/recordings/{recording_id}/upload-session",
    response_model=UploadSessionResponse,
)
def create_upload_session(
    contribution_id: str,
    recording_id: str,
    payload: UploadSessionRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> UploadSessionResponse:
    contribution = owned_contribution(db, current_user, contribution_id)
    recording = next((item for item in contribution.recordings if item.id == recording_id), None)
    if recording is None:
        raise ApiError("NOT_FOUND", "Repetition introuvable.", 404)
    wants_video = bool(contribution.consent_snapshot.get("wants_video"))
    if payload.include_video and not wants_video:
        raise ApiError("VIDEO_CONSENT_REQUIRED", "La video n'est pas autorisee.", 403)
    storage = ObjectStorage()
    expires = get_settings().dataset_presigned_url_expire_seconds
    landmark = UploadTarget(
        object_key=recording.landmark_object_key,
        upload_url=storage.presigned_put_url(
            PRIVATE_LANDMARK_BUCKET, recording.landmark_object_key, payload.landmark_content_type
        ),
        expires_in_seconds=expires,
        content_type=payload.landmark_content_type,
    )
    video = None
    if payload.include_video and recording.video_object_key and payload.video_content_type:
        video = UploadTarget(
            object_key=recording.video_object_key,
            upload_url=storage.presigned_put_url(
                PRIVATE_VIDEO_BUCKET, recording.video_object_key, payload.video_content_type
            ),
            expires_in_seconds=expires,
            content_type=payload.video_content_type,
        )
    contribution.status = ContributionStatus.UPLOADING
    db.commit()
    return UploadSessionResponse(recording_id=recording.id, landmark=landmark, video=video)


@router.post(
    "/{contribution_id}/recordings/{recording_id}/confirm-upload", response_model=RecordingResponse
)
def confirm_upload(
    contribution_id: str,
    recording_id: str,
    payload: ConfirmUploadRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ContributionRecording:
    contribution = owned_contribution(db, current_user, contribution_id)
    recording = next((item for item in contribution.recordings if item.id == recording_id), None)
    if recording is None:
        raise ApiError("NOT_FOUND", "Repetition introuvable.", 404)
    if payload.checksum_landmarks.lower() != recording.checksum_landmarks.lower():
        raise ApiError("CHECKSUM_MISMATCH", "Checksum landmarks incorrect.", 422)
    if recording.checksum_video and payload.checksum_video != recording.checksum_video:
        raise ApiError("CHECKSUM_MISMATCH", "Checksum video incorrect.", 422)
    recording.landmark_size_bytes = payload.landmark_size_bytes
    recording.file_size_bytes = payload.video_size_bytes
    recording.upload_confirmed_at = datetime.now(UTC)
    contribution.status = ContributionStatus.READY_TO_SUBMIT
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="UPLOAD_CONFIRMED",
            target_type="ContributionRecording",
            target_id=recording.id,
            details={
                "landmark_size_bytes": payload.landmark_size_bytes,
                "video_size_bytes": payload.video_size_bytes,
            },
        )
    )
    db.commit()
    db.refresh(recording)
    return recording


@router.post("/{contribution_id}/submit", response_model=ContributionResponse)
def submit_contribution(
    contribution_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.CONTRIBUTOR, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    contribution = owned_contribution(db, current_user, contribution_id)
    if contribution.status not in {
        ContributionStatus.READY_TO_SUBMIT,
        ContributionStatus.UPLOADING,
    }:
        raise ApiError("INVALID_STATUS", "Contribution pas prete pour l'envoi.", 409)
    if len(contribution.recordings) < contribution.campaign.minimum_repetitions_per_submission:
        raise ApiError(
            "INSUFFICIENT_REPETITIONS",
            "Nombre de repetitions insuffisant.",
            422,
            {"minimum": contribution.campaign.minimum_repetitions_per_submission},
        )
    if any(
        recording.automatic_quality_status == AutomaticQualityStatus.FAILED
        for recording in contribution.recordings
    ):
        raise ApiError(
            "AUTOMATIC_CHECK_FAILED", "Une repetition a echoue au controle automatique.", 422
        )
    if any(recording.upload_confirmed_at is None for recording in contribution.recordings):
        raise ApiError("UPLOAD_INCOMPLETE", "Tous les fichiers doivent etre confirmes.", 422)
    contribution.status = ContributionStatus.PENDING_LINGUIST_REVIEW
    contribution.submitted_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="CONTRIBUTION_SUBMITTED",
            target_type="DatasetContribution",
            target_id=contribution.id,
            details={"recording_count": len(contribution.recordings)},
        )
    )
    db.commit()
    return owned_contribution(db, current_user, contribution_id)


@router.post("/{contribution_id}/revoke", response_model=ContributionResponse)
def revoke_contribution(
    contribution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    contribution = owned_contribution(db, current_user, contribution_id)
    if contribution.status == ContributionStatus.ARCHIVED:
        raise ApiError("REVOKE_NOT_ALLOWED", "Contribution archivee.", 409)
    contribution.status = ContributionStatus.REVOKED
    contribution.revoked_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="CONTRIBUTION_REVOKED",
            target_type="DatasetContribution",
            target_id=contribution.id,
            details={},
        )
    )
    db.commit()
    return owned_contribution(db, current_user, contribution_id)
