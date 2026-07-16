import csv
import io
import json
import random
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import (
    AuditLog,
    CampaignSign,
    ContributionRecording,
    DatasetContribution,
    DatasetVersion,
    DatasetVersionItem,
)
from app.models.enums import ContributionStatus, DatasetSplit, DatasetVersionStatus, UserRoleName
from app.models.sign import Sign
from app.models.user import User
from app.schemas.dataset import DatasetVersionCreateRequest, DatasetVersionResponse
from app.services.object_storage import DATASET_EXPORT_BUCKET, ObjectStorage

router = APIRouter(prefix="/admin/datasets", tags=["admin-datasets"])


def approved_recordings(db: Session) -> list[ContributionRecording]:
    return list(
        db.scalars(
            select(ContributionRecording)
            .join(ContributionRecording.contribution)
            .options(
                selectinload(ContributionRecording.contribution).selectinload(
                    DatasetContribution.contributor
                ),
                selectinload(ContributionRecording.contribution)
                .selectinload(DatasetContribution.campaign_sign)
                .selectinload(CampaignSign.sign)
                .selectinload(Sign.category),
            )
            .where(
                DatasetContribution.status == ContributionStatus.APPROVED,
                DatasetContribution.revoked_at.is_(None),
                ContributionRecording.upload_confirmed_at.is_not(None),
            )
            .order_by(ContributionRecording.created_at.asc())
        )
    )


def split_by_contributor(
    recordings: list[ContributionRecording], seed: int
) -> dict[str, DatasetSplit]:
    contributor_ids = sorted(
        {recording.contribution.contributor.public_id for recording in recordings}
    )
    rng = random.Random(seed)
    rng.shuffle(contributor_ids)
    total = len(contributor_ids)
    train_cut = max(1, round(total * 0.7)) if total else 0
    validation_cut = train_cut + max(0, round(total * 0.15))
    splits: dict[str, DatasetSplit] = {}
    for index, public_id in enumerate(contributor_ids):
        if index < train_cut:
            splits[public_id] = DatasetSplit.TRAIN
        elif index < validation_cut:
            splits[public_id] = DatasetSplit.VALIDATION
        else:
            splits[public_id] = DatasetSplit.TEST
    return splits


def build_manifest(
    recordings: list[ContributionRecording], splits: dict[str, DatasetSplit]
) -> tuple[str, str]:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "recording_id",
            "anonymous_contributor_id",
            "sign_id",
            "sign_code",
            "campaign_id",
            "landmark_path",
            "video_path",
            "split",
            "duration_ms",
            "quality_score",
            "feature_schema_version",
            "dominant_hand",
            "region",
            "consent_level",
            "checksum_landmarks",
            "checksum_video",
        ],
    )
    writer.writeheader()
    for recording in recordings:
        contribution = recording.contribution
        profile = contribution.contributor
        campaign_sign = contribution.campaign_sign
        writer.writerow(
            {
                "recording_id": recording.id,
                "anonymous_contributor_id": profile.public_id,
                "sign_id": campaign_sign.sign_id,
                "sign_code": campaign_sign.sign.code,
                "campaign_id": contribution.campaign_id,
                "landmark_path": recording.landmark_object_key,
                "video_path": recording.video_object_key or "",
                "split": splits[profile.public_id].value,
                "duration_ms": recording.duration_ms,
                "quality_score": recording.quality_score,
                "feature_schema_version": recording.feature_schema_version,
                "dominant_hand": profile.dominant_hand.value if profile.dominant_hand else "",
                "region": profile.region or "",
                "consent_level": "landmarks+video" if recording.video_object_key else "landmarks",
                "checksum_landmarks": recording.checksum_landmarks,
                "checksum_video": recording.checksum_video or "",
            }
        )
    stats = {
        "recording_count": len(recordings),
        "contributor_count": len(
            {recording.contribution.contributor.public_id for recording in recordings}
        ),
        "sign_count": len(
            {recording.contribution.campaign_sign.sign_id for recording in recordings}
        ),
        "duration_ms_total": sum(recording.duration_ms for recording in recordings),
        "quality_average": (
            sum(recording.quality_score for recording in recordings) / len(recordings)
            if recordings
            else 0
        ),
        "splits": {split.value: list(splits.values()).count(split) for split in DatasetSplit},
    }
    return buffer.getvalue(), json.dumps(stats, ensure_ascii=False, indent=2)


@router.get("", response_model=list[DatasetVersionResponse])
def list_datasets(
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[DatasetVersion]:
    return list(db.scalars(select(DatasetVersion).order_by(DatasetVersion.created_at.desc())))


@router.post("", response_model=DatasetVersionResponse, status_code=201)
def create_dataset(
    payload: DatasetVersionCreateRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.ADMIN, UserRoleName.ML_REVIEWER))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetVersion:
    version = DatasetVersion(
        name=payload.name,
        semantic_version=payload.semantic_version,
        description=payload.description,
        feature_schema_version=payload.feature_schema_version,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("/{dataset_version_id}", response_model=DatasetVersionResponse)
def get_dataset(
    dataset_version_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ADMIN, UserRoleName.ML_REVIEWER))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetVersion:
    version = db.scalar(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
    if version is None:
        raise ApiError("NOT_FOUND", "Version dataset introuvable.", 404)
    return version


@router.post("/{dataset_version_id}/build", response_model=DatasetVersionResponse)
def build_dataset(
    dataset_version_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.ADMIN, UserRoleName.ML_REVIEWER))
    ],
    db: Annotated[Session, Depends(get_db)],
    seed: int = 42,
) -> DatasetVersion:
    version = db.scalar(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
    if version is None:
        raise ApiError("NOT_FOUND", "Version dataset introuvable.", 404)
    version.status = DatasetVersionStatus.BUILDING
    recordings = [
        recording
        for recording in approved_recordings(db)
        if recording.feature_schema_version == version.feature_schema_version
    ]
    splits = split_by_contributor(recordings, seed)
    manifest, statistics = build_manifest(recordings, splits)
    for item in list(version.items):
        db.delete(item)
    for recording in recordings:
        split = splits[recording.contribution.contributor.public_id]
        db.add(
            DatasetVersionItem(
                dataset_version_id=version.id, recording_id=recording.id, split=split
            )
        )
    version.sign_count = len(
        {recording.contribution.campaign_sign.sign_id for recording in recordings}
    )
    version.recording_count = len(recordings)
    version.contributor_count = len(
        {recording.contribution.contributor.public_id for recording in recordings}
    )
    version.manifest_object_key = f"datasets/{version.name}/{version.semantic_version}/manifest.csv"
    version.statistics_object_key = (
        f"datasets/{version.name}/{version.semantic_version}/statistics.json"
    )
    ObjectStorage().put_text(
        DATASET_EXPORT_BUCKET, version.manifest_object_key, manifest, "text/csv"
    )
    ObjectStorage().put_text(
        DATASET_EXPORT_BUCKET, version.statistics_object_key, statistics, "application/json"
    )
    version.status = DatasetVersionStatus.READY
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="DATASET_BUILT",
            target_type="DatasetVersion",
            target_id=version.id,
            details={"recording_count": version.recording_count, "seed": seed},
        )
    )
    db.commit()
    db.refresh(version)
    return version


@router.post("/{dataset_version_id}/validate", response_model=DatasetVersionResponse)
def validate_dataset(
    dataset_version_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ADMIN, UserRoleName.ML_REVIEWER))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetVersion:
    version = db.scalar(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
    if version is None:
        raise ApiError("NOT_FOUND", "Version dataset introuvable.", 404)
    if version.manifest_object_key is None:
        raise ApiError("DATASET_NOT_BUILT", "Construisez le dataset avant validation.", 409)
    version.status = DatasetVersionStatus.READY
    db.commit()
    db.refresh(version)
    return version


@router.post("/{dataset_version_id}/publish", response_model=DatasetVersionResponse)
def publish_dataset(
    dataset_version_id: str,
    current_user: Annotated[User, Depends(require_roles(UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetVersion:
    version = db.scalar(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
    if version is None:
        raise ApiError("NOT_FOUND", "Version dataset introuvable.", 404)
    if version.status != DatasetVersionStatus.READY:
        raise ApiError("DATASET_NOT_READY", "Le dataset n'est pas pret a publier.", 409)
    version.status = DatasetVersionStatus.PUBLISHED
    version.published_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="DATASET_PUBLISHED",
            target_type="DatasetVersion",
            target_id=version.id,
            details={},
        )
    )
    db.commit()
    db.refresh(version)
    return version


@router.post("/{dataset_version_id}/archive", response_model=DatasetVersionResponse)
def archive_dataset(
    dataset_version_id: str,
    current_user: Annotated[User, Depends(require_roles(UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetVersion:
    version = db.scalar(select(DatasetVersion).where(DatasetVersion.id == dataset_version_id))
    if version is None:
        raise ApiError("NOT_FOUND", "Version dataset introuvable.", 404)
    version.status = DatasetVersionStatus.ARCHIVED
    version.archived_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="DATASET_ARCHIVED",
            target_type="DatasetVersion",
            target_id=version.id,
            details={},
        )
    )
    db.commit()
    db.refresh(version)
    return version
