"""Modelo AuditLog (sin soft delete según diccionario)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from vulncentral_db.base import Base, BigIntPk

if TYPE_CHECKING:
    from vulncentral_db.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigIntPk, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id],
    )

    @validates("action", "entity")
    def _validate_len_255(self, key: str, value: str) -> str:
        if value is None:
            raise ValueError(f"{key} requerido")
        s = value.strip()
        if not s:
            raise ValueError(f"{key} no puede estar vacío")
        if len(s) > 255:
            raise ValueError(f"{key} excede 255 caracteres")
        return s
