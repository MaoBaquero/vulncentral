"""Listado de roles para UI (combobox)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.role import Role
from app.models.user import User
from app.rbac import USE_CASE_USUARIOS, require_permission_any
from app.schemas.role import RoleRead

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(
    _: Annotated[User, Depends(require_permission_any(USE_CASE_USUARIOS, ("r", "c")))],
    db: Session = Depends(get_db),
) -> list[Role]:
    return list(
        db.scalars(
            select(Role).where(Role.deleted_at.is_(None)).order_by(Role.id),
        ).all(),
    )
