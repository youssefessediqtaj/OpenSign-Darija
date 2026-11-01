from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.api.v1.system import api_health
from app.core.config import get_settings
from app.core.errors import error_payload, install_error_handlers
from app.services.contribution_request_protection import contribution_payload_size_error
from app.services.request_protection import recognition_payload_size_error


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)

    @app.middleware("http")
    async def reject_oversized_uploads_before_body_parsing(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if (
            request.method == "POST"
            and request.url.path
            in {"/api/v1/recognitions/word", "/api/v1/recognitions/colors-experimental"}
            and (error := recognition_payload_size_error(request))
        ):
            return JSONResponse(
                status_code=error.status_code,
                content=error_payload(error.code, error.message, error.details),
            )
        if (
            request.method == "POST"
            and request.url.path == "/api/v1/contributions"
            and (error := contribution_payload_size_error(request))
        ):
            return JSONResponse(
                status_code=error.status_code,
                content=error_payload(error.code, error.message, error.details),
            )
        return await call_next(request)

    app.include_router(api_router)
    if settings.colors_experimental_enabled and len(settings.colors_experimental_token) >= 16:
        from app.api.v1.colors_experimental import router as colors_router

        app.include_router(colors_router, prefix="/api/v1")
    app.add_api_route("/health", api_health, methods=["GET"])
    return app


app = create_app()
