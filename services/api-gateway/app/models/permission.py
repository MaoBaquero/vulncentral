"""Modelo Permission (columnas SQL c, r, u, d para CRUD)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, false, ForeignKey, Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.use_case import UseCase


class Permission(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    use_case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("use_cases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    perm_c: Mapped[bool] = mapped_column(
        "c",
        Boolean,
        nullable=False,
        server_default=false(),
    )
    perm_r: Mapped[bool] = mapped_column(
        "r",
        Boolean,
        nullable=False,
        server_default=false(),
    )
    perm_u: Mapped[bool] = mapped_column(
        "u",
        Boolean,
        nullable=False,
        server_default=false(),
    )
    perm_d: Mapped[bool] = mapped_column(
        "d",
        Boolean,
        nullable=False,
        server_default=false(),
    )

    role: Mapped[Role] = relationship(
        "Role",
        back_populates="permissions",
        foreign_keys=[role_id],
    )
    use_case: Mapped[UseCase] = relationship(
        "UseCase",
        back_populates="permissions",
        foreign_keys=[use_case_id],
    )

    @validates("name")
    def _validate_name(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return None
        s = value.strip()
        if not s:
            return None
        if len(s) > 255:
            raise ValueError("name excede 255 caracteres")
        return s
