"""Exige Content-Type application/json en escrituras /api/v1 con cuerpo (Fase 8)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.errors_format import error_payload


class JsonContentTypeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PATCH", "PUT"):
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/v1"):
            return await call_next(request)
        try:
            content_length = int(request.headers.get("content-length") or "0")
        except ValueError:
            content_length = -1
        if content_length <= 0:
            return await call_next(request)
        ct = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if ct != "application/json":
            return JSONResponse(
                status_code=415,
                content=error_payload(
                    "unsupported_media_type",
                    "Se requiere Content-Type: application/json para el cuerpo de esta solicitud.",
                ),
            )
        return await call_next(request)
