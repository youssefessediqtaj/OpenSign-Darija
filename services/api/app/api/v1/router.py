from fastapi import APIRouter

from app.api.v1 import (
    admin_datasets,
    admin_models,
    auth,
    consents,
    contribution_campaigns,
    contributions,
    contributors,
    linguistics,
    messages,
    recognitions,
    reviews,
    signs,
    speech,
    system,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(signs.router)
api_router.include_router(recognitions.router)
api_router.include_router(recognitions.models_router)
api_router.include_router(messages.router)
api_router.include_router(speech.router)
api_router.include_router(linguistics.router)
api_router.include_router(consents.router)
api_router.include_router(contributors.router)
api_router.include_router(contribution_campaigns.router)
api_router.include_router(contributions.router)
api_router.include_router(reviews.router)
api_router.include_router(admin_datasets.router)
api_router.include_router(admin_models.router)
