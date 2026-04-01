"""Rate limiting (Fase 8 — OWASP, fuerza bruta en login)."""

from __future__ import annotations

import os

from fastapi import Request
from slowapi import Limiter


def _remote_ip(request: Request) -> str:
    xf = request.headers.get("X-Forwarded-For")
    if xf:
        return xf.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _rate_limit_enabled() -> bool:
    v = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower()
    return v not in ("0", "false", "no", "off")


def _login_limit_string() -> str:
    raw = os.getenv("RATE_LIMIT_LOGIN", "5/minute").strip()
    if raw.lower() in ("0", "off", "none"):
        return "10000/minute"
    return raw or "5/minute"


limiter = Limiter(key_func=_remote_ip, enabled=_rate_limit_enabled())
LOGIN_LIMIT = _login_limit_string()

__all__ = ["limiter", "LOGIN_LIMIT"]
