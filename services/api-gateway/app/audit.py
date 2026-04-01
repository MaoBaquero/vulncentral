"""Escritura en audit_logs (Fase 8 — sin datos sensibles en action/entity)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def record_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    commit: bool = True,
) -> None:
    """
    Registra un evento de auditoría. `action` y `entity` deben ser cadenas cortas
    sin contraseñas, tokens ni PII innecesaria (solo identificadores técnicos).
    """
    a = (action or "").strip()[:255]
    e = (entity or "").strip()[:255]
    if not a or not e:
        return
    try:
        db.add(AuditLog(user_id=user_id, action=a, entity=e))
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception:
        logger.exception("Fallo al escribir audit_log (no aborta la petición principal)")
        db.rollback()
