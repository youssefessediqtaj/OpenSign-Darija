from fastapi import APIRouter

from app.api.v1 import auth, recognitions, signs, system

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(signs.router)
api_router.include_router(recognitions.router)
