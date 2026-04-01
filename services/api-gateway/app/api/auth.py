"""Login y perfil (JWT)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.deps import get_current_user, get_db
from app.errors_format import error_payload
from app.models.user import User
from app.rbac import permissions_matrix_for_role
from app.rate_limit import LOGIN_LIMIT, limiter
from app.security.jwt_tokens import create_access_token
from app.security.password import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str | int]:
    email = (form_data.username or "").strip().lower()
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
        )
    )
    if user is None or not verify_password(form_data.password, user.password):
        record_audit(
            db,
            user_id=user.id if user else None,
            action="login_failed",
            entity="auth",
            commit=True,
        )
        return JSONResponse(
            status_code=401,
            content=error_payload("invalid_credentials", "Credenciales incorrectas."),
        )
    if user.role_id is None:
        record_audit(
            db,
            user_id=user.id,
            action="login_failed_no_role",
            entity="auth",
            commit=True,
        )
        return JSONResponse(
            status_code=401,
            content=error_payload("invalid_credentials", "Credenciales incorrectas."),
        )
    try:
        token, expires_in = create_access_token(user.id, user.role_id)
    except RuntimeError:
        logger.error("Error de configuración JWT (JWT_SECRET u algoritmo)")
        return JSONResponse(
            status_code=500,
            content=error_payload(
                "configuration_error",
                "Error de configuración del servidor.",
            ),
        )
    record_audit(
        db,
        user_id=user.id,
        action="login_success",
        entity="auth",
        commit=True,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.get("/me")
def me(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | int | None | list]:
    return {
        "id": current.id,
        "name": current.name,
        "email": current.email,
        "role_id": current.role_id,
        "role_name": current.role.name if current.role else None,
        "permissions": permissions_matrix_for_role(db, current.role_id),
    }
