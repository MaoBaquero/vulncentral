"""Control de acceso por objeto (IDOR) para roles con alcance restringido (Fase 8)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.errors_format import error_payload
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.models.vulnerability import Vulnerability

GLOBAL_DATA_ROLES = frozenset({"Administrator", "Master"})


def has_global_data_access(user: User) -> bool:
    if user.role is None or user.role.name is None:
        return False
    return user.role.name in GLOBAL_DATA_ROLES


def has_cross_project_read(user: User) -> bool:
    """Lectura/listado de proyectos y recursos enlazados en cualquier propietario (RBAC sigue limitando mutaciones)."""
    if has_global_data_access(user):
        return True
    if user.role is None or user.role.name is None:
        return False
    return user.role.name == "Inspector"


def visible_project_ids(db: Session, user: User) -> set[int] | None:
    """None = sin filtro (acceso global). Conjunto vacío posible si el usuario no tiene proyectos."""
    if has_cross_project_read(user):
        return None
    ids = db.scalars(
        select(Project.id).where(
            Project.user_id == user.id,
            Project.deleted_at.is_(None),
        ),
    ).all()
    return set(ids)


def get_project_for_read(db: Session, user: User, project_id: int) -> Project:
    from fastapi import HTTPException, status

    p = db.scalar(
        select(Project)
        .options(joinedload(Project.owner))
        .where(Project.id == project_id, Project.deleted_at.is_(None)),
    )
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Proyecto no encontrado."),
        )
    if not has_cross_project_read(user) and p.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Proyecto no encontrado."),
        )
    return p


def get_scan_for_read(db: Session, user: User, scan_id: int) -> Scan:
    from fastapi import HTTPException, status

    s = db.scalar(
        select(Scan)
        .options(joinedload(Scan.project))
        .where(Scan.id == scan_id, Scan.deleted_at.is_(None)),
    )
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    if has_cross_project_read(user):
        return s
    p = db.scalar(
        select(Project).where(Project.id == s.project_id, Project.deleted_at.is_(None)),
    )
    if p is None or p.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Escaneo no encontrado."),
        )
    return s


def get_vulnerability_for_read(db: Session, user: User, vuln_id: int) -> Vulnerability:
    from fastapi import HTTPException, status

    v = db.scalar(
        select(Vulnerability)
        .options(joinedload(Vulnerability.scan))
        .where(
            Vulnerability.id == vuln_id,
            Vulnerability.deleted_at.is_(None),
        ),
    )
    if v is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    if has_cross_project_read(user):
        return v
    s = db.scalar(
        select(Scan).where(Scan.id == v.scan_id, Scan.deleted_at.is_(None)),
    )
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    p = db.scalar(
        select(Project).where(Project.id == s.project_id, Project.deleted_at.is_(None)),
    )
    if p is None or p.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Vulnerabilidad no encontrada."),
        )
    return v


def ensure_project_owner_for_mutate(db: Session, user: User, project_id: int) -> Project:
    """Igual que lectura: roles globales o propietario del proyecto."""
    return get_project_for_read(db, user, project_id)
