"""Saneado de texto antes de persistir (sin tocar contraseñas ni emails)."""

from __future__ import annotations

import html
import re


def sanitize_text(value: str | None, *, escape_html: bool = True) -> str | None:
    if value is None:
        return None
    s = value.strip()
    if not s:
        return s
    s = re.sub(r"\s+", " ", s)
    if escape_html:
        return html.escape(s, quote=True)
    return s


def sanitize_plain_line(value: str | None) -> str | None:
    """Strip y colapso de espacios; sin escape HTML (p. ej. nombres cortos)."""
    return sanitize_text(value, escape_html=False)
