"""API Gateway VulnCentral — salud, JWT, RBAC (Fase 3) y API /api/v1 CRUD + Trivy (Fase 4)."""

from __future__ import annotations

import logging
import os
import sys

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router
from app.api.v1 import api_v1_router
from app.errors_format import error_payload
from app.middleware.jwt_auth import JWTAuthMiddleware
from app.middleware.json_content_type import JsonContentTypeMiddleware
from app.rate_limit import limiter

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:80",
            "http://127.0.0.1:80",
            "http://localhost:5173",
        ]
    return [part.strip() for part in raw.split(",") if part.strip()]


def create_app() -> FastAPI:
    application = FastAPI(
        title="VulnCentral API Gateway",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.state.limiter = limiter

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(
        _request: Request,
        _exc: RateLimitExceeded,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_payload(
                "rate_limited",
                "Demasiadas solicitudes. Intente de nuevo más tarde.",
            ),
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(JsonContentTypeMiddleware)
    application.add_middleware(JWTAuthMiddleware)

    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail) if exc.detail else "",
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Error de validación en la solicitud.",
                    "details": exc.errors(),
                }
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Error no controlado (detalle solo en servidor)")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Error interno del servidor.",
                }
            },
        )

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"service": "vulncentral-api-gateway"}

    application.include_router(auth_router)
    application.include_router(api_v1_router)

    return application


app = create_app()
