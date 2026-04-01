"""CRUD /api/v1/scans e ingesta Trivy (informe vía volumen + cola; ver services/worker/trivy_processing.py)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_client import enqueue_ingest_trivy_json
from app.deps import get_db
from app.errors_format import error_payload
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.rbac import USE_CASE_ESCANEOS, require_permission
from app.sanitize import sanitize_text
from app.schemas.scan import ScanCreate, ScanRead, ScanUpdate
from app.schemas.trivy import TrivyReport, TrivyReportQueued

router = APIRouter(prefix="/scans", tags=["scans"])


def _get_scan(db: Session, scan_id: int) -> Scan | None:
    return db.scalar(
        select(Scan).where(Scan.id == scan_id, Scan.deleted_at.is_(None)),
    )


def _ensure_project(db: Session, project_id: int) -> None:
    p = db.scalar(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Proyecto no válido o inexistente."),
        )


@router.get("", response_model=list[ScanRead])
def list_scans(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "r"))],
    db: Session = Depends(get_db),
) -> list[Scan]:
    return list(
        db.scalars(select(Scan).where(Scan.deleted_at.is_(None)).order_by(Scan.id)).all(),
    )


@router.post("", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
def create_scan(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "c"))],
    body: ScanCreate,
    db: Session = Depends(get_db),
) -> Scan:
    _ensure_project(db, body.project_id)
    tool_s = sanitize_text(body.tool, escape_html=False) or ""
    status_s = sanitize_text(body.status, escape_html=False) or ""
    s = Scan(project_id=body.project_id, tool=tool_s, status=status_s)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "r"))],
    scan_id: int,
    db: Session = Depends(get_db),
) -> Scan:
    s = _get_scan(db, scan_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    return s


@router.patch("/{scan_id}", response_model=ScanRead)
def update_scan(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "u"))],
    scan_id: int,
    body: ScanUpdate,
    db: Session = Depends(get_db),
) -> Scan:
    s = _get_scan(db, scan_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    data = body.model_dump(exclude_unset=True)
    if "project_id" in data and data["project_id"] is not None:
        _ensure_project(db, data["project_id"])
        s.project_id = data["project_id"]
    if "tool" in data and data["tool"] is not None:
        s.tool = sanitize_text(data["tool"], escape_html=False) or ""
    if "status" in data and data["status"] is not None:
        s.status = sanitize_text(data["status"], escape_html=False) or ""
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "d"))],
    scan_id: int,
    db: Session = Depends(get_db),
) -> None:
    s = _get_scan(db, scan_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    s.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.post(
    "/{scan_id}/trivy-report",
    response_model=TrivyReportQueued,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_trivy_report(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "u"))],
    scan_id: int,
    report: TrivyReport,
    db: Session = Depends(get_db),
) -> TrivyReportQueued:
    s = _get_scan(db, scan_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    reports_dir = Path(os.getenv("REPORTS_DIR", "/app/data/reports")).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"scan_{scan_id}_{uuid.uuid4().hex}.json"
    out_path = reports_dir / filename
    out_path.write_text(report.model_dump_json(), encoding="utf-8")
    abs_path = str(out_path.resolve())
    correlation_id = str(uuid.uuid4())
    async_result = enqueue_ingest_trivy_json(scan_id, abs_path, correlation_id=correlation_id)
    return TrivyReportQueued(
        task_id=str(async_result.id),
        file_path=abs_path,
        correlation_id=correlation_id,
    )
