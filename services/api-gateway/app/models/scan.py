"""Modelo Scan."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.vulnerability import Vulnerability


class Scan(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tool: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    project: Mapped[Project] = relationship(
        "Project",
        back_populates="scans",
        foreign_keys=[project_id],
    )
    vulnerabilities: Mapped[list[Vulnerability]] = relationship(
        "Vulnerability",
        back_populates="scan",
        foreign_keys="Vulnerability.scan_id",
    )

    @validates("tool")
    def _validate_tool(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("tool requerido")
        s = value.strip()
        if not s:
            raise ValueError("tool no puede estar vacío")
        if len(s) > 255:
            raise ValueError("tool excede 255 caracteres")
        return s

    @validates("status")
    def _validate_status(self, _key: str, value: str) -> str:
        if value is None:
            raise ValueError("status requerido")
        s = value.strip()
        if not s:
            raise ValueError("status no puede estar vacío")
        if len(s) > 50:
            raise ValueError("status excede 50 caracteres")
        return s
