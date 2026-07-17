from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import ExternalDatasetImport, ExternalDatasetLabel, ExternalDatasetSource
from app.models.enums import (
    ExternalDatasetLabelStatus,
    ExternalDatasetLicenseStatus,
    ExternalDatasetSourceStatus,
    UserRoleName,
)
from app.models.user import User
from app.schemas.external_datasets import (
    ExternalDatasetActionResponse,
    ExternalDatasetImportResponse,
    ExternalDatasetLabelResponse,
    ExternalDatasetLabelUpdateRequest,
    ExternalDatasetSourceResponse,
)

router = APIRouter(prefix="/admin/external-datasets", tags=["admin-external-datasets"])


def import_response(item: ExternalDatasetImport) -> ExternalDatasetImportResponse:
    return ExternalDatasetImportResponse(
        id=item.id,
        source_id=item.source_id,
        status=item.status,
        archive_checksum=item.archive_checksum,
        file_count=item.file_count,
        total_size_bytes=item.total_size_bytes,
        report_path=item.report_path,
        started_at=item.started_at,
        completed_at=item.completed_at,
        error_code=item.error_code,
    )


def label_response(item: ExternalDatasetLabel) -> ExternalDatasetLabelResponse:
    return ExternalDatasetLabelResponse(
        id=item.id,
        source_id=item.source_id,
        original_label=item.original_label,
        normalized_label=item.normalized_label,
        canonical_sign_id=item.canonical_sign_id,
        semantic_concept_id=item.semantic_concept_id,
        class_code=item.class_code,
        status=item.status.value,
        sample_count=item.sample_count,
        signer_count=item.signer_count,
        metadata=item.label_metadata,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def source_response(source: ExternalDatasetSource) -> ExternalDatasetSourceResponse:
    latest_import = max(source.imports, key=lambda item: item.started_at, default=None)
    return ExternalDatasetSourceResponse(
        id=source.id,
        code=source.code,
        name=source.name,
        provider=source.provider.value,
        version=source.version,
        doi=source.doi,
        task_type=source.task_type.value,
        modality=source.modality.value,
        license=source.license,
        license_status=source.license_status.value,
        source_metadata=source.source_metadata,
        checksum=source.checksum,
        status=source.status.value,
        imported_at=source.imported_at,
        validated_at=source.validated_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
        label_count=len(source.labels),
        latest_import=import_response(latest_import) if latest_import else None,
    )


def load_source(db: Session, source_id: str) -> ExternalDatasetSource:
    source = db.scalar(
        select(ExternalDatasetSource)
        .options(
            selectinload(ExternalDatasetSource.labels),
            selectinload(ExternalDatasetSource.imports),
        )
        .where(ExternalDatasetSource.code == source_id)
    )
    if source is None:
        source = db.scalar(
            select(ExternalDatasetSource)
            .options(
                selectinload(ExternalDatasetSource.labels),
                selectinload(ExternalDatasetSource.imports),
            )
            .where(ExternalDatasetSource.id == source_id)
        )
    if source is None:
        raise ApiError("NOT_FOUND", "Source externe introuvable.", 404)
    return source


@router.get("", response_model=list[ExternalDatasetSourceResponse])
def list_sources(
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExternalDatasetSourceResponse]:
    sources = db.scalars(
        select(ExternalDatasetSource)
        .options(
            selectinload(ExternalDatasetSource.labels),
            selectinload(ExternalDatasetSource.imports),
        )
        .order_by(ExternalDatasetSource.code.asc())
    ).all()
    return [source_response(source) for source in sources]


@router.get("/{source_id}", response_model=ExternalDatasetSourceResponse)
def get_source(
    source_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ExternalDatasetSourceResponse:
    return source_response(load_source(db, source_id))


@router.post("/{source_id}/audit", response_model=ExternalDatasetActionResponse)
def audit_source(
    source_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ExternalDatasetActionResponse:
    source = load_source(db, source_id)
    if source.imported_at is None:
        return ExternalDatasetActionResponse(
            source_id=source.code,
            status=source.status.value,
            message="Aucune archive locale importée; lancez les scripts ML d'import avant l'audit.",
            details={"requires_local_data": True},
        )
    source.status = ExternalDatasetSourceStatus.AUDITING
    db.commit()
    return ExternalDatasetActionResponse(
        source_id=source.code,
        status=source.status.value,
        message="Audit demandé; utilisez make dataset-audit-external pour produire les rapports.",
    )


@router.post("/{source_id}/validate", response_model=ExternalDatasetActionResponse)
def validate_source(
    source_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ExternalDatasetActionResponse:
    source = load_source(db, source_id)
    if source.license_status != ExternalDatasetLicenseStatus.VERIFIED:
        source.status = ExternalDatasetSourceStatus.LICENSE_PENDING
        db.commit()
        raise ApiError("LICENSE_NOT_VERIFIED", "Licence externe non validée.", 409)
    if source.imported_at is None:
        raise ApiError(
            "SOURCE_NOT_IMPORTED",
            "Importez et auditez la source avant validation.",
            409,
        )
    source.status = ExternalDatasetSourceStatus.VALIDATED
    source.validated_at = datetime.now(UTC)
    db.commit()
    return ExternalDatasetActionResponse(
        source_id=source.code,
        status=source.status.value,
        message=(
            "Source validée pour prétraitement; l'entraînement exige encore "
            "des labels approuvés."
        ),
    )


@router.post("/{source_id}/build", response_model=ExternalDatasetActionResponse)
def build_source(
    source_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ExternalDatasetActionResponse:
    source = load_source(db, source_id)
    if source.status not in {
        ExternalDatasetSourceStatus.VALIDATED,
        ExternalDatasetSourceStatus.PREPROCESSING,
        ExternalDatasetSourceStatus.READY,
    }:
        raise ApiError("SOURCE_NOT_VALIDATED", "La source doit être validée avant build.", 409)
    return ExternalDatasetActionResponse(
        source_id=source.code,
        status=source.status.value,
        message="Build externe à exécuter via Makefile pour conserver les datasets hors API.",
    )


@router.get("/{source_id}/labels", response_model=list[ExternalDatasetLabelResponse])
def list_labels(
    source_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.LINGUIST_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExternalDatasetLabelResponse]:
    source = load_source(db, source_id)
    return [
        label_response(label)
        for label in sorted(source.labels, key=lambda item: item.original_label)
    ]


@router.patch("/{source_id}/labels/{label_id}", response_model=ExternalDatasetLabelResponse)
def update_label(
    source_id: str,
    label_id: str,
    payload: ExternalDatasetLabelUpdateRequest,
    _: Annotated[User, Depends(require_roles(UserRoleName.LINGUIST_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ExternalDatasetLabelResponse:
    source = load_source(db, source_id)
    label = db.scalar(
        select(ExternalDatasetLabel).where(
            ExternalDatasetLabel.id == label_id,
            ExternalDatasetLabel.source_id == source.id,
        )
    )
    if label is None:
        raise ApiError("NOT_FOUND", "Label externe introuvable.", 404)
    if payload.normalized_label is not None:
        label.normalized_label = payload.normalized_label
    if payload.canonical_sign_id is not None:
        label.canonical_sign_id = payload.canonical_sign_id
    if payload.semantic_concept_id is not None:
        label.semantic_concept_id = payload.semantic_concept_id
    if payload.class_code is not None:
        label.class_code = payload.class_code
    if payload.status is not None:
        label.status = ExternalDatasetLabelStatus(payload.status)
    if payload.notes:
        label.label_metadata = {**label.label_metadata, "review_notes": payload.notes}
    db.commit()
    db.refresh(label)
    return label_response(label)
