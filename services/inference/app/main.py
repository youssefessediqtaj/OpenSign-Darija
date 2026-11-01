from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(router)
    if settings.colors_experimental_enabled and len(settings.colors_experimental_token) >= 16:
        from app.api.colors_experimental import router as colors_router

        app.include_router(colors_router)
    return app


app = create_app()
