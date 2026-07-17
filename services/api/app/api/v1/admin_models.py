from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import AuditLog
from app.models.enums import ModelStatus, UserRoleName
from app.models.sign import ModelVersion
from app.models.user import User
from app.schemas.recognition import ActiveModelResponse

router = APIRouter(prefix="/admin/models", tags=["admin-models"])


def to_model_response(model: ModelVersion) -> ActiveModelResponse:
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


@router.get("", response_model=list[ActiveModelResponse])
def list_models(
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[ActiveModelResponse]:
    models = db.scalars(select(ModelVersion).order_by(ModelVersion.created_at.desc())).all()
    return [to_model_response(model) for model in models]


@router.get("/{model_id}", response_model=ActiveModelResponse)
def get_model(
    model_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveModelResponse:
    model = db.get(ModelVersion, model_id)
    if model is None:
        raise ApiError("NOT_FOUND", "Modele introuvable.", 404)
    return to_model_response(model)


@router.post("/{model_id}/validate", response_model=ActiveModelResponse)
def validate_model(
    model_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveModelResponse:
    model = db.get(ModelVersion, model_id)
    if model is None:
        raise ApiError("NOT_FOUND", "Modele introuvable.", 404)
    if not model.artifact_path or not model.checksum or model.vocabulary_size <= 0:
        raise ApiError("MODEL_ARTIFACT_INCOMPLETE", "Artefacts modele incomplets.", 409)
    model.status = ModelStatus.READY
    model.validated_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="MODEL_VALIDATED",
            target_type="ModelVersion",
            target_id=model.id,
            details={"name": model.name, "version": model.semantic_version},
        )
    )
    db.commit()
    db.refresh(model)
    return to_model_response(model)


@router.post("/{model_id}/activate", response_model=ActiveModelResponse)
def activate_model(
    model_id: str,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveModelResponse:
    model = db.get(ModelVersion, model_id)
    if model is None:
        raise ApiError("NOT_FOUND", "Modele introuvable.", 404)
    if model.status != ModelStatus.READY:
        raise ApiError("MODEL_NOT_READY", "Seul un modele READY peut etre active.", 409)
    if not model.artifact_path or not model.checksum:
        raise ApiError("MODEL_ARTIFACT_INCOMPLETE", "Artefacts modele incomplets.", 409)
    for active in db.scalars(
        select(ModelVersion).where(
            ModelVersion.name == model.name, ModelVersion.is_active.is_(True)
        )
    ):
        active.is_active = False
        active.status = ModelStatus.ARCHIVED
        active.archived_at = datetime.now(UTC)
    model.is_active = True
    model.status = ModelStatus.ACTIVE
    model.activated_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="MODEL_ACTIVATED",
            target_type="ModelVersion",
            target_id=model.id,
            details={"name": model.name, "version": model.semantic_version},
        )
    )
    db.commit()
    db.refresh(model)
    return to_model_response(model)


@router.post("/{model_id}/archive", response_model=ActiveModelResponse)
def archive_model(
    model_id: str,
    current_user: Annotated[User, Depends(require_roles(UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveModelResponse:
    model = db.get(ModelVersion, model_id)
    if model is None:
        raise ApiError("NOT_FOUND", "Modele introuvable.", 404)
    model.is_active = False
    model.status = ModelStatus.ARCHIVED
    model.archived_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="MODEL_ARCHIVED",
            target_type="ModelVersion",
            target_id=model.id,
            details={},
        )
    )
    db.commit()
    db.refresh(model)
    return to_model_response(model)


@router.post("/{model_id}/rollback", response_model=ActiveModelResponse)
def rollback_model(
    model_id: str,
    current_user: Annotated[User, Depends(require_roles(UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> ActiveModelResponse:
    current = db.get(ModelVersion, model_id)
    if current is None:
        raise ApiError("NOT_FOUND", "Modele introuvable.", 404)
    previous = db.scalar(
        select(ModelVersion)
        .where(
            ModelVersion.name == current.name,
            ModelVersion.id != current.id,
            ModelVersion.status.in_([ModelStatus.READY, ModelStatus.ARCHIVED]),
            ModelVersion.artifact_path != "",
            ModelVersion.checksum != "",
        )
        .order_by(ModelVersion.activated_at.desc().nullslast(), ModelVersion.created_at.desc())
    )
    if previous is None:
        raise ApiError("ROLLBACK_UNAVAILABLE", "Aucune version precedente valide.", 409)
    current.is_active = False
    current.status = ModelStatus.ARCHIVED
    previous.is_active = True
    previous.status = ModelStatus.ACTIVE
    previous.activated_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="MODEL_ROLLBACK",
            target_type="ModelVersion",
            target_id=previous.id,
            details={"from": current.id, "to": previous.id},
        )
    )
    db.commit()
    db.refresh(previous)
    return to_model_response(previous)
