"""Modelos ORM — importar para registrar metadata (Alembic)."""

from vulncentral_db.base import Base
from vulncentral_db.models.audit_log import AuditLog
from vulncentral_db.models.permission import Permission
from vulncentral_db.models.project import Project
from vulncentral_db.models.role import Role
from vulncentral_db.models.scan import Scan
from vulncentral_db.models.use_case import UseCase
from vulncentral_db.models.user import User
from vulncentral_db.models.vulnerability import Vulnerability

__all__ = [
    "AuditLog",
    "Base",
    "Permission",
    "Project",
    "Role",
    "Scan",
    "UseCase",
    "User",
    "Vulnerability",
]
