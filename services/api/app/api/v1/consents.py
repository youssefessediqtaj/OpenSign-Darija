from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import AuditLog, ConsentRecord, ConsentTemplate
from app.models.user import User
from app.schemas.dataset import ConsentCreateRequest, ConsentRecordResponse, ConsentTemplateResponse

router = APIRouter(prefix="/consents", tags=["consents"])


def hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    salt = get_settings().jwt_secret_key
    return sha256(f"{salt}:{value}".encode()).hexdigest()


@router.get("/templates", response_model=list[ConsentTemplateResponse])
def list_templates(
    db: Annotated[Session, Depends(get_db)], language: str = "fr"
) -> list[ConsentTemplate]:
    templates = list(
        db.scalars(
            select(ConsentTemplate)
            .where(ConsentTemplate.is_active.is_(True), ConsentTemplate.language == language)
            .order_by(ConsentTemplate.code, ConsentTemplate.version)
        )
    )
    if not templates and language != "fr":
        templates = list(
            db.scalars(
                select(ConsentTemplate)
                .where(ConsentTemplate.is_active.is_(True), ConsentTemplate.language == "fr")
                .order_by(ConsentTemplate.code, ConsentTemplate.version)
            )
        )
    return templates


@router.get("/me", response_model=list[ConsentRecordResponse])
def my_consents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ConsentRecord]:
    return list(
        db.scalars(
            select(ConsentRecord)
            .options(selectinload(ConsentRecord.template))
            .where(ConsentRecord.user_id == current_user.id)
            .order_by(ConsentRecord.created_at.desc())
        )
    )


@router.post("", response_model=list[ConsentRecordResponse], status_code=201)
def create_consents(
    payload: ConsentCreateRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ConsentRecord]:
    template = db.scalar(
        select(ConsentTemplate).where(
            ConsentTemplate.id == payload.consent_template_id,
            ConsentTemplate.is_active.is_(True),
        )
    )
    if template is None:
        raise ApiError("CONSENT_TEMPLATE_NOT_FOUND", "Modele de consentement introuvable.", 404)
    now = datetime.now(UTC)
    records: list[ConsentRecord] = []
    for choice in payload.choices:
        record = ConsentRecord(
            user_id=current_user.id,
            consent_template_id=template.id,
            consent_type=choice.consent_type,
            granted=choice.granted,
            granted_at=now if choice.granted else None,
            evidence={
                "template_code": template.code,
                "template_version": template.version,
                "language": payload.language,
                "choice": choice.granted,
                "app_version": get_settings().app_version,
                **payload.evidence,
            },
            ip_hash=hash_optional(request.client.host if request.client else None),
            user_agent_hash=hash_optional(request.headers.get("user-agent")),
        )
        db.add(record)
        records.append(record)
        db.add(
            AuditLog(
                actor_user_id=current_user.id,
                action="CONSENT_GRANTED" if choice.granted else "CONSENT_DECLINED",
                target_type="ConsentRecord",
                target_id=record.id,
                details={"consent_type": choice.consent_type.value},
            )
        )
    db.commit()
    for record in records:
        db.refresh(record)
    return records


@router.post("/{consent_id}/revoke", response_model=ConsentRecordResponse)
def revoke_consent(
    consent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsentRecord:
    record = db.scalar(
        select(ConsentRecord)
        .options(selectinload(ConsentRecord.template))
        .where(ConsentRecord.id == consent_id, ConsentRecord.user_id == current_user.id)
    )
    if record is None:
        raise ApiError("NOT_FOUND", "Consentement introuvable.", 404)
    record.granted = False
    record.revoked_at = datetime.now(UTC)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="CONSENT_REVOKED",
            target_type="ConsentRecord",
            target_id=record.id,
            details={"consent_type": record.consent_type.value},
        )
    )
    db.commit()
    db.refresh(record)
    return record
