from fastapi import APIRouter

from app.api.v1 import (
    admin_datasets,
    auth,
    consents,
    contribution_campaigns,
    contributions,
    contributors,
    recognitions,
    reviews,
    signs,
    system,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(signs.router)
api_router.include_router(recognitions.router)
api_router.include_router(consents.router)
api_router.include_router(contributors.router)
api_router.include_router(contribution_campaigns.router)
api_router.include_router(contributions.router)
api_router.include_router(reviews.router)
api_router.include_router(admin_datasets.router)
