"""
Datos iniciales: use_cases → roles → permissions → usuario elmero.

Orden de inserción según especificación Fase 3. Idempotente por nombre/email.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.use_case import UseCase
from app.models.user import User
from app.security.password import hash_password

logger = logging.getLogger(__name__)

USE_CASE_NAMES: list[str] = [
    "Gestor usuarios",
    "Gestor proyectos",
    "Gestor escaneos",
    "Gestor vulnerabilidades",
    "Gestor logs",
]

ROLE_NAMES: list[str] = ["Administrator", "Master", "Inspector"]

# (role_name, use_case_name, c, r, u, d) — orden filas 1–15 del spec
PERMISSION_ROWS: list[tuple[str, str, bool, bool, bool, bool]] = [
    ("Administrator", "Gestor usuarios", True, True, True, True),
    ("Administrator", "Gestor proyectos", False, True, True, True),
    ("Administrator", "Gestor escaneos", False, True, True, True),
    ("Administrator", "Gestor vulnerabilidades", False, True, True, True),
    ("Administrator", "Gestor logs", False, True, False, False),
    ("Master", "Gestor usuarios", False, False, False, False),
    ("Master", "Gestor proyectos", True, True, True, True),
    ("Master", "Gestor escaneos", True, True, True, True),
    ("Master", "Gestor vulnerabilidades", True, True, True, True),
    ("Master", "Gestor logs", False, False, False, False),
    ("Inspector", "Gestor usuarios", False, False, False, False),
    ("Inspector", "Gestor proyectos", False, True, False, False),
    ("Inspector", "Gestor escaneos", False, True, True, True),
    ("Inspector", "Gestor vulnerabilidades", True, True, True, True),
    ("Inspector", "Gestor logs", False, False, False, False),
]

INITIAL_USER = {
    "name": "elmero",
    "email": "elmero@admon.com",
    "password_plain": "elmero/*-",
}


def run_seed(db: Session) -> dict[str, Any]:
    """Inserta o actualiza filas necesarias. No hace commit."""
    summary: dict[str, Any] = {"use_cases": 0, "roles": 0, "permissions": 0, "user": None}
    is_sqlite = db.bind.dialect.name == "sqlite"

    for idx, name in enumerate(USE_CASE_NAMES, start=1):
        existing = db.scalar(select(UseCase).where(UseCase.name == name))
        if existing is None:
            if is_sqlite:
                db.add(UseCase(id=idx, name=name))
            else:
                db.add(UseCase(name=name))
            summary["use_cases"] += 1
    db.flush()

    for idx, name in enumerate(ROLE_NAMES, start=1):
        existing = db.scalar(select(Role).where(Role.name == name))
        if existing is None:
            if is_sqlite:
                db.add(Role(id=idx, name=name))
            else:
                db.add(Role(name=name))
            summary["roles"] += 1
    db.flush()

    role_ids = {r.name: r.id for r in db.scalars(select(Role)).all()}
    uc_ids = {u.name: u.id for u in db.scalars(select(UseCase)).all()}

    for row_idx, (rn, un, c, r_, u_, d_) in enumerate(PERMISSION_ROWS, start=1):
        rid, uid = role_ids[rn], uc_ids[un]
        perm = db.scalar(
            select(Permission).where(
                Permission.role_id == rid,
                Permission.use_case_id == uid,
            )
        )
        if perm is None:
            kwargs = dict(
                role_id=rid,
                use_case_id=uid,
                perm_c=c,
                perm_r=r_,
                perm_u=u_,
                perm_d=d_,
            )
            if is_sqlite:
                kwargs["id"] = row_idx
            db.add(Permission(**kwargs))
            summary["permissions"] += 1
        else:
            perm.perm_c = c
            perm.perm_r = r_
            perm.perm_u = u_
            perm.perm_d = d_

    admin_id = role_ids["Administrator"]
    user = db.scalar(select(User).where(User.email == INITIAL_USER["email"]))
    if user is None:
        u_kwargs: dict[str, Any] = dict(
            name=INITIAL_USER["name"],
            email=INITIAL_USER["email"],
            password=hash_password("__seed_placeholder__"),
            role_id=admin_id,
        )
        if is_sqlite:
            u_kwargs["id"] = 1
        user = User(**u_kwargs)
        user.set_password(INITIAL_USER["password_plain"])
        db.add(user)
        summary["user"] = "created"
    else:
        user.name = INITIAL_USER["name"]
        user.role_id = admin_id
        user.set_password(INITIAL_USER["password_plain"])
        if user.deleted_at is not None:
            user.deleted_at = None
        summary["user"] = "updated"

    return summary


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        out = run_seed(db)
        db.commit()
        logger.info("Seed completado: %s", out)
    except Exception:
        db.rollback()
        logger.exception("Fallo en seed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
