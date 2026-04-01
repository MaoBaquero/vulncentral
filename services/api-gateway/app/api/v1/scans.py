"""CRUD /api/v1/scans e ingesta Trivy (informe vía volumen + cola; ver services/worker/trivy_processing.py)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.celery_client import enqueue_ingest_trivy_json
from app.deps import get_db
from app.idor import get_project_for_read, get_scan_for_read, visible_project_ids
from app.models.scan import Scan
from app.models.user import User
from app.rbac import USE_CASE_ESCANEOS, require_permission
from app.sanitize import sanitize_text
from app.schemas.scan import ScanCreate, ScanRead, ScanUpdate
from app.schemas.trivy import TrivyReport, TrivyReportQueued

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanRead])
def list_scans(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "r"))],
    db: Session = Depends(get_db),
) -> list[Scan]:
    q = select(Scan).where(Scan.deleted_at.is_(None))
    vis = visible_project_ids(db, current)
    if vis is not None:
        if not vis:
            return []
        q = q.where(Scan.project_id.in_(vis))
    return list(db.scalars(q.order_by(Scan.id)).all())


@router.post("", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
def create_scan(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "c"))],
    body: ScanCreate,
    db: Session = Depends(get_db),
) -> Scan:
    get_project_for_read(db, current, body.project_id)
    tool_s = sanitize_text(body.tool, escape_html=False) or ""
    status_s = sanitize_text(body.status, escape_html=False) or ""
    s = Scan(project_id=body.project_id, tool=tool_s, status=status_s)
    db.add(s)
    db.commit()
    db.refresh(s)
    record_audit(
        db,
        user_id=current.id,
        action="scan_create",
        entity=f"scan:{s.id}",
        commit=True,
    )
    return s


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "r"))],
    scan_id: int,
    db: Session = Depends(get_db),
) -> Scan:
    return get_scan_for_read(db, current, scan_id)


@router.patch("/{scan_id}", response_model=ScanRead)
def update_scan(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "u"))],
    scan_id: int,
    body: ScanUpdate,
    db: Session = Depends(get_db),
) -> Scan:
    s = get_scan_for_read(db, current, scan_id)
    data = body.model_dump(exclude_unset=True)
    if "project_id" in data and data["project_id"] is not None:
        get_project_for_read(db, current, data["project_id"])
        s.project_id = data["project_id"]
    if "tool" in data and data["tool"] is not None:
        s.tool = sanitize_text(data["tool"], escape_html=False) or ""
    if "status" in data and data["status"] is not None:
        s.status = sanitize_text(data["status"], escape_html=False) or ""
    db.commit()
    db.refresh(s)
    record_audit(
        db,
        user_id=current.id,
        action="scan_update",
        entity=f"scan:{scan_id}",
        commit=True,
    )
    return s


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "d"))],
    scan_id: int,
    db: Session = Depends(get_db),
) -> None:
    s = get_scan_for_read(db, current, scan_id)
    s.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(
        db,
        user_id=current.id,
        action="scan_delete",
        entity=f"scan:{scan_id}",
        commit=True,
    )


@router.post(
    "/{scan_id}/trivy-report",
    response_model=TrivyReportQueued,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_trivy_report(
    current: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "u"))],
    scan_id: int,
    report: TrivyReport,
    db: Session = Depends(get_db),
) -> TrivyReportQueued:
    get_scan_for_read(db, current, scan_id)
    reports_dir = Path(os.getenv("REPORTS_DIR", "/app/data/reports")).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"scan_{scan_id}_{uuid.uuid4().hex}.json"
    out_path = reports_dir / filename
    out_path.write_text(report.model_dump_json(), encoding="utf-8")
    abs_path = str(out_path.resolve())
    correlation_id = str(uuid.uuid4())
    async_result = enqueue_ingest_trivy_json(scan_id, abs_path, correlation_id=correlation_id)
    record_audit(
        db,
        user_id=current.id,
        action="trivy_report_queued",
        entity=f"scan:{scan_id}",
        commit=True,
    )
    return TrivyReportQueued(
        task_id=str(async_result.id),
        file_path=abs_path,
        correlation_id=correlation_id,
    )
