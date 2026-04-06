"""CRUD /api/v1/vulnerabilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.audit import record_audit
from app.deps import get_db
from app.errors_format import error_payload
from app.idor import (
    get_scan_for_read,
    get_vulnerability_for_read,
    visible_project_ids,
)
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


@router.get("", response_model=list[VulnerabilityRead])
def list_vulnerabilities(
    current: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "r"))],
    db: Session = Depends(get_db),
) -> list[Vulnerability]:
    vis = visible_project_ids(db, current)
    if vis is None:
        return list(
            db.scalars(
                select(Vulnerability)
                .options(joinedload(Vulnerability.scan))
                .where(Vulnerability.deleted_at.is_(None))
                .order_by(Vulnerability.id),
            ).all(),
        )
    if not vis:
        return []
    return list(
        db.scalars(
            select(Vulnerability)
            .options(joinedload(Vulnerability.scan))
            .join(Scan, Vulnerability.scan_id == Scan.id)
            .where(
                Vulnerability.deleted_at.is_(None),
                Scan.deleted_at.is_(None),
                Scan.project_id.in_(vis),
            )
            .order_by(Vulnerability.id),
        ).all(),
    )


@router.post("", response_model=VulnerabilityRead, status_code=status.HTTP_201_CREATED)
def create_vulnerability(
    current: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "c"))],
    body: VulnerabilityCreate,
    db: Session = Depends(get_db),
) -> Vulnerability:
    get_scan_for_read(db, current, body.scan_id)
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
    record_audit(
        db,
        user_id=current.id,
        action="vulnerability_create",
        entity=f"vulnerability:{v.id}",
        commit=True,
    )
    return v


@router.get("/{vuln_id}", response_model=VulnerabilityRead)
def get_vulnerability(
    current: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "r"))],
    vuln_id: int,
    db: Session = Depends(get_db),
) -> Vulnerability:
    return get_vulnerability_for_read(db, current, vuln_id)


@router.patch("/{vuln_id}", response_model=VulnerabilityRead)
def update_vulnerability(
    current: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "u"))],
    vuln_id: int,
    body: VulnerabilityUpdate,
    db: Session = Depends(get_db),
) -> Vulnerability:
    v = get_vulnerability_for_read(db, current, vuln_id)
    data = body.model_dump(exclude_unset=True)
    if "scan_id" in data and data["scan_id"] is not None:
        get_scan_for_read(db, current, data["scan_id"])
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
    record_audit(
        db,
        user_id=current.id,
        action="vulnerability_update",
        entity=f"vulnerability:{vuln_id}",
        commit=True,
    )
    return v


@router.delete("/{vuln_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vulnerability(
    current: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "d"))],
    vuln_id: int,
    db: Session = Depends(get_db),
) -> None:
    v = get_vulnerability_for_read(db, current, vuln_id)
    v.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(
        db,
        user_id=current.id,
        action="vulnerability_delete",
        entity=f"vulnerability:{vuln_id}",
        commit=True,
    )
