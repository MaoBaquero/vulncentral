"""CRUD /api/v1/projects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.deps import get_db
from app.errors_format import error_payload
from app.idor import get_project_for_read, has_global_data_access, visible_project_ids
from app.models.project import Project
from app.models.user import User
from app.rbac import USE_CASE_PROYECTOS, require_permission
from app.sanitize import sanitize_text
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def _ensure_user(db: Session, user_id: int) -> None:
    u = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_payload("validation_error", "Usuario no válido o inexistente."),
        )


@router.get("", response_model=list[ProjectRead])
def list_projects(
    current: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "r"))],
    db: Session = Depends(get_db),
) -> list[Project]:
    q = select(Project).where(Project.deleted_at.is_(None))
    vis = visible_project_ids(db, current)
    if vis is not None:
        if not vis:
            return []
        q = q.where(Project.id.in_(vis))
    return list(db.scalars(q.order_by(Project.id)).all())


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    current: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "c"))],
    body: ProjectCreate,
    db: Session = Depends(get_db),
) -> Project:
    if not has_global_data_access(current) and body.user_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                "forbidden",
                "Solo puede crear proyectos asociados a su propio usuario.",
            ),
        )
    _ensure_user(db, body.user_id)
    desc = sanitize_text(body.description, escape_html=True) if body.description is not None else None
    name_s = sanitize_text(body.name, escape_html=True) or ""
    p = Project(user_id=body.user_id, name=name_s, description=desc)
    db.add(p)
    db.commit()
    db.refresh(p)
    record_audit(
        db,
        user_id=current.id,
        action="project_create",
        entity=f"project:{p.id}",
        commit=True,
    )
    return p


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    current: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "r"))],
    project_id: int,
    db: Session = Depends(get_db),
) -> Project:
    return get_project_for_read(db, current, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    current: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "u"))],
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
) -> Project:
    p = get_project_for_read(db, current, project_id)
    data = body.model_dump(exclude_unset=True)
    if "user_id" in data and data["user_id"] is not None:
        if not has_global_data_access(current) and data["user_id"] != current.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload("forbidden", "No puede reasignar el proyecto a otro usuario."),
            )
        _ensure_user(db, data["user_id"])
        p.user_id = data["user_id"]
    if "name" in data and data["name"] is not None:
        p.name = sanitize_text(data["name"], escape_html=True) or ""
    if "description" in data:
        if data["description"] is None:
            p.description = None
        else:
            p.description = sanitize_text(data["description"], escape_html=True)
    db.commit()
    db.refresh(p)
    record_audit(
        db,
        user_id=current.id,
        action="project_update",
        entity=f"project:{project_id}",
        commit=True,
    )
    return p


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    current: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "d"))],
    project_id: int,
    db: Session = Depends(get_db),
) -> None:
    p = get_project_for_read(db, current, project_id)
    p.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(
        db,
        user_id=current.id,
        action="project_delete",
        entity=f"project:{project_id}",
        commit=True,
    )
