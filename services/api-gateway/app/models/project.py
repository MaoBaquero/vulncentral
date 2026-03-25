"""Modelo Project."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.scan import Scan
    from app.models.user import User


class Project(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped[User] = relationship(
        "User",
        back_populates="projects",
        foreign_keys=[user_id],
    )
    scans: Mapped[list[Scan]] = relationship(
        "Scan",
        back_populates="project",
        foreign_keys="Scan.project_id",
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
