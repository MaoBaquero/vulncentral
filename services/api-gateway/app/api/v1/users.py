"""CRUD /api/v1/users."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.deps import get_db
from app.errors_format import error_payload
from app.models.role import Role
from app.models.user import User
from app.rbac import USE_CASE_USUARIOS, require_permission
from app.sanitize import sanitize_text
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _get_user(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).where(User.id == user_id, User.deleted_at.is_(None)),
    )


@router.get("", response_model=list[UserRead])
def list_users(
    _: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "r"))],
    db: Session = Depends(get_db),
) -> list[User]:
    return list(
        db.scalars(select(User).where(User.deleted_at.is_(None)).order_by(User.id)).all(),
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    actor: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "c"))],
    body: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    email = str(body.email).strip().lower()
    dup = db.scalar(
        select(User).where(User.email == email, User.deleted_at.is_(None)),
    )
    if dup is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_payload("conflict", "Ya existe un usuario con ese email."),
        )
    if body.role_id is not None:
        role = db.scalar(
            select(Role).where(Role.id == body.role_id, Role.deleted_at.is_(None)),
        )
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_payload("validation_error", "Rol no válido."),
            )
    name_s = sanitize_text(body.name, escape_html=True) or ""
    u = User(
        name=name_s,
        email=email,
        role_id=body.role_id,
    )
    u.set_password(body.password)
    db.add(u)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(u)
    record_audit(
        db,
        user_id=actor.id,
        action="user_create",
        entity=f"user:{u.id}",
        commit=True,
    )
    return u


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    _: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "r"))],
    user_id: int,
    db: Session = Depends(get_db),
) -> User:
    u = _get_user(db, user_id)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Usuario no encontrado."),
        )
    return u


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    actor: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "u"))],
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
) -> User:
    u = _get_user(db, user_id)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Usuario no encontrado."),
        )
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        email = str(data["email"]).strip().lower()
        dup = db.scalar(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
                User.id != user_id,
            ),
        )
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_payload("conflict", "Ya existe un usuario con ese email."),
            )
        u.email = email
    if "name" in data and data["name"] is not None:
        u.name = sanitize_text(data["name"], escape_html=True) or ""
    if "password" in data and data["password"] is not None:
        u.set_password(data["password"])
    if "role_id" in data:
        rid = data["role_id"]
        if rid is not None:
            role = db.scalar(select(Role).where(Role.id == rid, Role.deleted_at.is_(None)))
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=error_payload("validation_error", "Rol no válido."),
                )
        u.role_id = rid
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(u)
    record_audit(
        db,
        user_id=actor.id,
        action="user_update",
        entity=f"user:{user_id}",
        commit=True,
    )
    return u


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    actor: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "d"))],
    user_id: int,
    db: Session = Depends(get_db),
) -> None:
    u = _get_user(db, user_id)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_payload("not_found", "Usuario no encontrado."),
        )
    u.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(
        db,
        user_id=actor.id,
        action="user_delete",
        entity=f"user:{user_id}",
        commit=True,
    )
