"""Login y perfil (JWT)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.errors_format import error_payload
from app.models.user import User
from app.security.jwt_tokens import create_access_token
from app.security.password import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
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
        return JSONResponse(
            status_code=401,
            content=error_payload("invalid_credentials", "Credenciales incorrectas."),
        )
    if user.role_id is None:
        return JSONResponse(
            status_code=401,
            content=error_payload("invalid_credentials", "Credenciales incorrectas."),
        )
    try:
        token, expires_in = create_access_token(user.id, user.role_id)
    except RuntimeError as e:
        logger.error("JWT: %s", e)
        return JSONResponse(
            status_code=500,
            content=error_payload(
                "configuration_error",
                "Error de configuración del servidor.",
            ),
        )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.get("/me")
def me(current: User = Depends(get_current_user)) -> dict[str, str | int | None]:
    return {
        "id": current.id,
        "name": current.name,
        "email": current.email,
        "role_id": current.role_id,
        "role_name": current.role.name if current.role else None,
    }
