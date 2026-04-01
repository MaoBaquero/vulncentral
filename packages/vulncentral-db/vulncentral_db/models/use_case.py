"""Modelo UseCase."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from vulncentral_db.base import Base, BigIntPk
from vulncentral_db.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from vulncentral_db.models.permission import Permission


class UseCase(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "use_cases"

    id: Mapped[int] = mapped_column(BigIntPk, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        back_populates="use_case",
        foreign_keys="Permission.use_case_id",
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
