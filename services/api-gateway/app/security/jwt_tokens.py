"""Creación y decodificación de JWT (HS256)."""

from __future__ import annotations

import os
import time
from typing import Any

import jwt

_DEFAULT_EXPIRE_MINUTES = 30


def _secret_and_alg() -> tuple[str, str]:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET no configurado")
    alg = os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"
    return secret, alg


def _expire_seconds() -> int:
    raw = os.getenv("JWT_EXPIRE_MINUTES", "").strip()
    if not raw:
        return _DEFAULT_EXPIRE_MINUTES * 60
    try:
        minutes = int(raw)
    except ValueError:
        return _DEFAULT_EXPIRE_MINUTES * 60
    return max(60, minutes * 60)


def create_access_token(user_id: int, role_id: int | None) -> tuple[str, int]:
    """Devuelve (token, expires_in_segundos)."""
    secret, alg = _secret_and_alg()
    now = int(time.time())
    exp = now + _expire_seconds()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": exp,
        "iat": now,
    }
    if role_id is not None:
        payload["role_id"] = role_id
    token = jwt.encode(payload, secret, algorithm=alg)
    if isinstance(token, bytes):
        token = token.decode("ascii")
    return token, exp - now


def decode_access_token(token: str) -> dict[str, Any]:
    secret, alg = _secret_and_alg()
    return jwt.decode(
        token,
        secret,
        algorithms=[alg],
        options={"require": ["exp", "sub"]},
    )
