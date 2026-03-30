"""RBAC: permisos por caso de uso (c/r/u/d) y rol."""

from __future__ import annotations

from typing import Literal

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.errors_format import error_payload
from app.models.permission import Permission
from app.models.use_case import UseCase
from app.models.user import User

PermAction = Literal["c", "r", "u", "d"]

USE_CASE_USUARIOS = "Gestor usuarios"
USE_CASE_PROYECTOS = "Gestor proyectos"
USE_CASE_ESCANEOS = "Gestor escaneos"
USE_CASE_VULNERABILIDADES = "Gestor vulnerabilidades"
USE_CASE_LOGS = "Gestor logs"

_PERM_ATTR = {"c": "perm_c", "r": "perm_r", "u": "perm_u", "d": "perm_d"}


def require_permission(use_case_name: str, action: PermAction):
    """Devuelve dependencia que exige permiso CRUD sobre el caso de uso."""

    def _check(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if user.role_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload("forbidden", "El usuario no tiene rol asignado."),
            )
        uc = db.scalar(
            select(UseCase).where(
                UseCase.name == use_case_name,
                UseCase.deleted_at.is_(None),
            )
        )
        if uc is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload("forbidden", "Caso de uso no disponible."),
            )
        perm = db.scalar(
            select(Permission).where(
                Permission.role_id == user.role_id,
                Permission.use_case_id == uc.id,
                Permission.deleted_at.is_(None),
            )
        )
        attr = _PERM_ATTR[action]
        allowed = perm is not None and bool(getattr(perm, attr))
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    "forbidden",
                    "No tiene permiso para realizar esta acción.",
                ),
            )
        return user

    return _check
