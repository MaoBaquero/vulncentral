"""CRUD /api/v1/scans e ingesta Trivy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.errors_format import error_payload
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.models.vulnerability import Vulnerability
from app.rbac import USE_CASE_ESCANEOS, require_permission
from app.sanitize import sanitize_text
from app.schemas.enums import Severity, VulnerabilityStatus
from app.schemas.scan import ScanCreate, ScanRead, ScanUpdate
from app.schemas.trivy import TrivyReport

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


def _map_trivy_severity(raw: str | None) -> Severity:
    if not raw:
        return Severity.MEDIUM
    u = raw.strip().upper()
    if u == "UNKNOWN":
        return Severity.LOW
    try:
        return Severity(u)
    except ValueError:
        return Severity.MEDIUM


def _truncate(s: str, max_len: int) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..." if max_len > 3 else s[:max_len]


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
    response_model=list[dict],
    status_code=status.HTTP_201_CREATED,
)
def ingest_trivy_report(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "u"))],
    scan_id: int,
    report: TrivyReport,
    db: Session = Depends(get_db),
) -> list[dict[str, int | str]]:
    s = _get_scan(db, scan_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    created: list[Vulnerability] = []
    default_status = VulnerabilityStatus.OPEN.value
    for result in report.Results:
        target = (result.Target or ".").strip() or "."
        fp = _truncate(sanitize_text(target, escape_html=False) or ".", 255)
        for tv in result.Vulnerabilities:
            vid = (tv.VulnerabilityID or "").strip() or "UNKNOWN"
            cve = _truncate(vid, 50)
            title_src = (tv.Title or tv.VulnerabilityID or tv.PkgName or "Finding").strip()
            title = _truncate(sanitize_text(title_src, escape_html=True) or "Finding", 255)
            desc_raw = tv.Description
            desc = None
            if desc_raw:
                desc = sanitize_text(desc_raw, escape_html=True)
            sev = _map_trivy_severity(tv.Severity)
            v = Vulnerability(
                scan_id=scan_id,
                title=title,
                description=desc,
                severity=sev.value,
                status=default_status,
                cve=cve,
                file_path=fp,
                line_number=0,
            )
            db.add(v)
            created.append(v)
    db.commit()
    for v in created:
        db.refresh(v)
    return [{"id": v.id, "cve": v.cve} for v in created]
