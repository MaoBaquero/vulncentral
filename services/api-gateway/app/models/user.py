"""Modelo User."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.project import Project

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    projects: Mapped[list[Project]] = relationship(
        "Project",
        back_populates="owner",
        foreign_keys="Project.user_id",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )

    @validates("name")
    def _validate_name(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("name requerido")
        s = value.strip()
        if not s:
            raise ValueError("name no puede estar vacío")
        if len(s) > 255:
            raise ValueError("name excede 255 caracteres")
        return s

    @validates("email")
    def _validate_email(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("email requerido")
        s = value.strip().lower()
        if len(s) > 255:
            raise ValueError("email excede 255 caracteres")
        if not _EMAIL_RE.match(s):
            raise ValueError("email inválido")
        return s

    @validates("password")
    def _validate_password(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("password requerido")
        if len(value) > 255:
            raise ValueError("password excede 255 caracteres")
        if not value.startswith("$2"):
            raise ValueError(
                "solo se almacenan hashes bcrypt; use set_password(plain) o hash_password()"
            )
        return value

    def set_password(self, plain: str) -> None:
        """Asigna la columna `password` con hash bcrypt."""
        from app.security.password import hash_password

        if not plain or not plain.strip():
            raise ValueError("contraseña vacía")
        self.password = hash_password(plain)
