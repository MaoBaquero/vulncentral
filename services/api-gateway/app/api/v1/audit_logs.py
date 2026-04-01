"""Listado de audit_logs (Gestor logs, solo lectura)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.rbac import USE_CASE_LOGS, require_permission

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity: str
    timestamp: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    skip: int
    limit: int


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    _: Annotated[User, Depends(require_permission(USE_CASE_LOGS, "r"))],
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> AuditLogListResponse:
    total = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    rows = db.scalars(
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .offset(skip)
        .limit(limit),
    ).all()
    return AuditLogListResponse(
        items=[AuditLogRead.model_validate(r) for r in rows],
        total=int(total),
        skip=skip,
        limit=limit,
    )
