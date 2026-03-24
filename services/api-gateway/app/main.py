"""Aplicación FastAPI mínima — sin lógica de negocio (Fase 1)."""

from __future__ import annotations

import logging
import os
import sys

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:80", "http://localhost:5173", "http://127.0.0.1:80"]
    return [part.strip() for part in raw.split(",") if part.strip()]


def create_app() -> FastAPI:
    application = FastAPI(
        title="VulnCentral API Gateway",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        logger.exception("Error no controlado: %s", exc)
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

    return application


app = create_app()
