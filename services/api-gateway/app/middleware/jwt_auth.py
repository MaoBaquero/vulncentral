"""Validación JWT para rutas protegidas (`/api/*`, `GET /auth/me`)."""

from __future__ import annotations

import logging

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.errors_format import error_payload
from app.middleware.body_size_limit import _max_trivy_body_bytes, is_post_trivy_report
from app.security.jwt_tokens import decode_access_token

logger = logging.getLogger(__name__)


def _path_requires_jwt(method: str, path: str) -> bool:
    if path == "/auth/me":
        return True
    if path.startswith("/api"):
        return True
    return False


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if is_post_trivy_report(request.method, path):
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    n = int(cl)
                except ValueError:
                    pass
                else:
                    limit = _max_trivy_body_bytes()
                    if n > limit:
                        return JSONResponse(
                            status_code=413,
                            content=error_payload(
                                "payload_too_large",
                                f"El cuerpo supera el máximo permitido ({limit} bytes).",
                            ),
                        )

        if not _path_requires_jwt(request.method, path):
            return await call_next(request)

        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content=error_payload(
                    "missing_token",
                    "Se requiere cabecera Authorization: Bearer <token>.",
                ),
            )
        token = auth.removeprefix("Bearer ").strip()
        if not token:
            return JSONResponse(
                status_code=401,
                content=error_payload("invalid_token", "Token vacío."),
            )
        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content=error_payload("token_expired", "El token ha expirado."),
            )
        except jwt.InvalidTokenError as e:
            logger.debug("JWT inválido: %s", e)
            return JSONResponse(
                status_code=401,
                content=error_payload("invalid_token", "Token inválido."),
            )
        except RuntimeError as e:
            logger.error("Configuración JWT: %s", e)
            return JSONResponse(
                status_code=500,
                content=error_payload("configuration_error", "Error de configuración del servidor."),
            )

        sub = payload.get("sub")
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            return JSONResponse(
                status_code=401,
                content=error_payload("invalid_token", "Token inválido."),
            )
        request.state.user_id = user_id
        return await call_next(request)
