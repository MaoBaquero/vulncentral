"""Límite de tamaño del cuerpo JSON para informes Trivy (usado desde JWT middleware)."""

from __future__ import annotations

import os


def _max_trivy_body_bytes() -> int:
    raw = os.getenv("MAX_JSON_BODY_BYTES")
    if raw is None or not raw.strip():
        return 10 * 1024 * 1024
    try:
        v = int(raw.strip())
        return v if v >= 1 else 10 * 1024 * 1024
    except ValueError:
        return 10 * 1024 * 1024


def is_post_trivy_report(request_method: str, path: str) -> bool:
    if request_method != "POST":
        return False
    p = path.rstrip("/")
    return p.endswith("/trivy-report") and "/scans/" in p
