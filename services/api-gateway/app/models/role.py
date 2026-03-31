"""Modelo Role."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base, BigIntPk
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User


class Role(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigIntPk, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        back_populates="role",
        foreign_keys="Permission.role_id",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
        foreign_keys="User.role_id",
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
