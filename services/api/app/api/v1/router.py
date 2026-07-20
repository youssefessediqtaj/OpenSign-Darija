from fastapi import APIRouter

from app.api.v1 import recognitions, speech, system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(recognitions.router)
api_router.include_router(speech.router)
