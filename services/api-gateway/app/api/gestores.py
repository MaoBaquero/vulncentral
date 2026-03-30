"""Rutas de ejemplo con RBAC por caso de uso (permiso de lectura `r`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.user import User
from app.rbac import (
    USE_CASE_ESCANEOS,
    USE_CASE_LOGS,
    USE_CASE_PROYECTOS,
    USE_CASE_USUARIOS,
    USE_CASE_VULNERABILIDADES,
    require_permission,
)

router = APIRouter(prefix="/api/gestores", tags=["rbac"])


@router.get("/usuarios")
def gestor_usuarios(
    _: Annotated[User, Depends(require_permission(USE_CASE_USUARIOS, "r"))],
) -> dict[str, str]:
    return {"use_case": USE_CASE_USUARIOS, "permission": "read"}


@router.get("/proyectos")
def gestor_proyectos(
    _: Annotated[User, Depends(require_permission(USE_CASE_PROYECTOS, "r"))],
) -> dict[str, str]:
    return {"use_case": USE_CASE_PROYECTOS, "permission": "read"}


@router.get("/escaneos")
def gestor_escaneos(
    _: Annotated[User, Depends(require_permission(USE_CASE_ESCANEOS, "r"))],
) -> dict[str, str]:
    return {"use_case": USE_CASE_ESCANEOS, "permission": "read"}


@router.get("/vulnerabilidades")
def gestor_vulnerabilidades(
    _: Annotated[User, Depends(require_permission(USE_CASE_VULNERABILIDADES, "r"))],
) -> dict[str, str]:
    return {"use_case": USE_CASE_VULNERABILIDADES, "permission": "read"}


@router.get("/logs")
def gestor_logs(
    _: Annotated[User, Depends(require_permission(USE_CASE_LOGS, "r"))],
) -> dict[str, str]:
    return {"use_case": USE_CASE_LOGS, "permission": "read"}
