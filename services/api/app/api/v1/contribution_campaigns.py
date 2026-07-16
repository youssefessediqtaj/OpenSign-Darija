from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ApiError
from app.db.session import get_db
from app.models.dataset import CampaignSign, CollectionCampaign
from app.models.enums import CampaignStatus
from app.models.sign import Sign
from app.schemas.dataset import CampaignResponse, CampaignSignResponse

router = APIRouter(prefix="/contribution-campaigns", tags=["contribution-campaigns"])


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(db: Annotated[Session, Depends(get_db)]) -> list[CollectionCampaign]:
    return list(
        db.scalars(
            select(CollectionCampaign)
            .where(CollectionCampaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.SCHEDULED]))
            .order_by(CollectionCampaign.created_at.desc())
        )
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str, db: Annotated[Session, Depends(get_db)]) -> CollectionCampaign:
    campaign = db.scalar(select(CollectionCampaign).where(CollectionCampaign.id == campaign_id))
    if campaign is None or campaign.status == CampaignStatus.ARCHIVED:
        raise ApiError("NOT_FOUND", "Campagne introuvable.", 404)
    return campaign


@router.get("/{campaign_id}/signs", response_model=list[CampaignSignResponse])
def list_campaign_signs(
    campaign_id: str, db: Annotated[Session, Depends(get_db)]
) -> list[CampaignSign]:
    campaign = db.scalar(select(CollectionCampaign).where(CollectionCampaign.id == campaign_id))
    if campaign is None or campaign.status == CampaignStatus.ARCHIVED:
        raise ApiError("NOT_FOUND", "Campagne introuvable.", 404)
    return list(
        db.scalars(
            select(CampaignSign)
            .options(selectinload(CampaignSign.sign).selectinload(Sign.category))
            .where(CampaignSign.campaign_id == campaign_id, CampaignSign.is_active.is_(True))
            .order_by(CampaignSign.created_at)
        )
    )
