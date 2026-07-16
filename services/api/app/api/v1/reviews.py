from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_roles
from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import AuditLog, CampaignSign, ContributionReview, DatasetContribution
from app.models.enums import ContributionStatus, ReviewDecision, ReviewType, UserRoleName
from app.models.sign import Sign
from app.models.user import User
from app.schemas.dataset import ContributionResponse, ReviewDecisionRequest, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["reviews"])


def review_query() -> Select[tuple[DatasetContribution]]:
    return select(DatasetContribution).options(
        selectinload(DatasetContribution.campaign),
        selectinload(DatasetContribution.campaign_sign)
        .selectinload(CampaignSign.sign)
        .selectinload(Sign.category),
        selectinload(DatasetContribution.recordings),
        selectinload(DatasetContribution.reviews),
    )


def get_review_contribution(db: Session, contribution_id: str) -> DatasetContribution:
    contribution: DatasetContribution | None = db.scalar(
        review_query().where(DatasetContribution.id == contribution_id)
    )
    if contribution is None:
        raise ApiError("NOT_FOUND", "Contribution introuvable.", 404)
    return contribution


@router.get("/linguistic/queue", response_model=list[ContributionResponse])
def linguistic_queue(
    _: Annotated[User, Depends(require_roles(UserRoleName.LINGUIST_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[DatasetContribution]:
    return list(
        db.scalars(
            review_query()
            .where(DatasetContribution.status == ContributionStatus.PENDING_LINGUIST_REVIEW)
            .order_by(DatasetContribution.submitted_at.asc())
        )
    )


@router.get("/linguistic/{contribution_id}", response_model=ContributionResponse)
def linguistic_detail(
    contribution_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.LINGUIST_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    return get_review_contribution(db, contribution_id)


@router.post("/linguistic/{contribution_id}/decision", response_model=ReviewResponse)
def linguistic_decision(
    contribution_id: str,
    payload: ReviewDecisionRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.LINGUIST_REVIEWER, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ContributionReview:
    contribution = get_review_contribution(db, contribution_id)
    if contribution.status != ContributionStatus.PENDING_LINGUIST_REVIEW:
        raise ApiError("INVALID_STATUS", "Contribution hors file linguistique.", 409)
    review = ContributionReview(
        contribution_id=contribution.id,
        recording_id=payload.recording_id,
        reviewer_id=current_user.id,
        review_type=ReviewType.LINGUISTIC,
        decision=payload.decision,
        reason_code=payload.reason_code,
        comment=payload.comment,
        review_metadata=payload.metadata,
    )
    if payload.decision == ReviewDecision.APPROVED:
        contribution.status = ContributionStatus.PENDING_ML_REVIEW
    elif payload.decision == ReviewDecision.REJECTED:
        contribution.status = ContributionStatus.LINGUIST_REJECTED
        contribution.completed_at = datetime.now(UTC)
    elif payload.decision == ReviewDecision.REVISION_REQUESTED:
        contribution.status = ContributionStatus.REVISION_REQUESTED
    else:
        contribution.status = ContributionStatus.PENDING_LINGUIST_REVIEW
    db.add(review)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="LINGUISTIC_REVIEW_DECISION",
            target_type="DatasetContribution",
            target_id=contribution.id,
            details={"decision": payload.decision.value, "reason_code": payload.reason_code},
        )
    )
    db.commit()
    db.refresh(review)
    return review


@router.get("/ml/queue", response_model=list[ContributionResponse])
def ml_queue(
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> list[DatasetContribution]:
    return list(
        db.scalars(
            review_query()
            .where(DatasetContribution.status == ContributionStatus.PENDING_ML_REVIEW)
            .order_by(DatasetContribution.submitted_at.asc())
        )
    )


@router.get("/ml/{contribution_id}", response_model=ContributionResponse)
def ml_detail(
    contribution_id: str,
    _: Annotated[User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> DatasetContribution:
    return get_review_contribution(db, contribution_id)


@router.post("/ml/{contribution_id}/decision", response_model=ReviewResponse)
def ml_decision(
    contribution_id: str,
    payload: ReviewDecisionRequest,
    current_user: Annotated[
        User, Depends(require_roles(UserRoleName.ML_REVIEWER, UserRoleName.ADMIN))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> ContributionReview:
    contribution = get_review_contribution(db, contribution_id)
    if contribution.status != ContributionStatus.PENDING_ML_REVIEW:
        raise ApiError("INVALID_STATUS", "Contribution hors file ML.", 409)
    review = ContributionReview(
        contribution_id=contribution.id,
        recording_id=payload.recording_id,
        reviewer_id=current_user.id,
        review_type=ReviewType.TECHNICAL,
        decision=payload.decision,
        reason_code=payload.reason_code,
        comment=payload.comment,
        review_metadata=payload.metadata,
    )
    if payload.decision == ReviewDecision.APPROVED:
        contribution.status = ContributionStatus.APPROVED
        contribution.completed_at = datetime.now(UTC)
    elif payload.decision == ReviewDecision.REJECTED:
        contribution.status = ContributionStatus.ML_REJECTED
        contribution.completed_at = datetime.now(UTC)
    elif payload.decision == ReviewDecision.REVISION_REQUESTED:
        contribution.status = ContributionStatus.REVISION_REQUESTED
    else:
        contribution.status = ContributionStatus.PENDING_ML_REVIEW
    db.add(review)
    db.add(
        AuditLog(
            actor_user_id=current_user.id,
            action="ML_REVIEW_DECISION",
            target_type="DatasetContribution",
            target_id=contribution.id,
            details={"decision": payload.decision.value, "reason_code": payload.reason_code},
        )
    )
    db.commit()
    db.refresh(review)
    return review
