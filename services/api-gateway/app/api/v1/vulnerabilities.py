"""CRUD /api/v1/vulnerabilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.errors_format import error_payload
from app.models.scan import Scan
from app.models.user import User
from app.models.vulnerability import Vulnerability
from app.rbac import USE_CASE_VULNERABILIDADES, require_permission
from app.sanitize import sanitize_text
from app.schemas.vulnerability import (
    VulnerabilityCreate,
    VulnerabilityRead,
    VulnerabilityUpdate,
)

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


def _get_vulnerability(db: Session, vuln_id: int) -> Vulnerability | None:
    return db.scalar(
        select(Vulnerability).where(
            Vulnerability.id == vuln_id,
            Vulnerability.deleted_at.is_(None),
        ),
    )


def _ensure_scan(db: Session, scan_id: int) -> None:
    s = db.scalar(select(Scan).where(Scan.id == scan_id, Scan.deleted_at.is_(None)))
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Escaneo no válido o inexistente."),
        )


@router.get("", response_model=list[VulnerabilityRead])
def list_vulnerabilities(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "r"))],
    db: Session = Depends(get_db),
) -> list[Vulnerability]:
    return list(
        db.scalars(
            select(Vulnerability)
            .where(Vulnerability.deleted_at.is_(None))
            .order_by(Vulnerability.id),
        ).all(),
    )


@router.post("", response_model=VulnerabilityRead, status_code=status.HTTP_201_CREATED)
def create_vulnerability(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "c"))],
    body: VulnerabilityCreate,
    db: Session = Depends(get_db),
) -> Vulnerability:
    _ensure_scan(db, body.scan_id)
    title_s = sanitize_text(body.title, escape_html=True) or ""
    desc = (
        sanitize_text(body.description, escape_html=True)
        if body.description is not None
        else None
    )
    cve_s = sanitize_text(body.cve, escape_html=False) or ""
    fp = sanitize_text(body.file_path, escape_html=False) or ""
    v = Vulnerability(
        scan_id=body.scan_id,
        title=title_s,
        description=desc,
        severity=body.severity.value,
        status=body.status.value,
        cve=cve_s,
        file_path=fp,
        line_number=body.line_number,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/{vuln_id}", response_model=VulnerabilityRead)
def get_vulnerability(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "r"))],
    vuln_id: int,
    db: Session = Depends(get_db),
) -> Vulnerability:
    v = _get_vulnerability(db, vuln_id)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    return v


@router.patch("/{vuln_id}", response_model=VulnerabilityRead)
def update_vulnerability(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "u"))],
    vuln_id: int,
    body: VulnerabilityUpdate,
    db: Session = Depends(get_db),
) -> Vulnerability:
    v = _get_vulnerability(db, vuln_id)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    data = body.model_dump(exclude_unset=True)
    if "scan_id" in data and data["scan_id"] is not None:
        _ensure_scan(db, data["scan_id"])
        v.scan_id = data["scan_id"]
    if "title" in data and data["title"] is not None:
        v.title = sanitize_text(data["title"], escape_html=True) or ""
    if "description" in data:
        if data["description"] is None:
            v.description = None
        else:
            v.description = sanitize_text(data["description"], escape_html=True)
    if "severity" in data and data["severity"] is not None:
        v.severity = data["severity"].value
    if "status" in data and data["status"] is not None:
        v.status = data["status"].value
    if "cve" in data and data["cve"] is not None:
        v.cve = sanitize_text(data["cve"], escape_html=False) or ""
    if "file_path" in data and data["file_path"] is not None:
        v.file_path = sanitize_text(data["file_path"], escape_html=False) or ""
    if "line_number" in data and data["line_number"] is not None:
        v.line_number = data["line_number"]
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vuln_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vulnerability(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "d"))],
    vuln_id: int,
    db: Session = Depends(get_db),
) -> None:
    v = _get_vulnerability(db, vuln_id)
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    v.deleted_at = datetime.now(timezone.utc)
    db.commit()
