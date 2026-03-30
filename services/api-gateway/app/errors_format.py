"""Formato JSON de errores alineado con los handlers de `main`."""

from __future__ import annotations

from typing import Any


def error_payload(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return {"error": err}
