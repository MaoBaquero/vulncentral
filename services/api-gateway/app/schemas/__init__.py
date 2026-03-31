"""Esquemas Pydantic de la API."""

from app.schemas.enums import Severity, VulnerabilityStatus
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.scan import ScanCreate, ScanRead, ScanUpdate
from app.schemas.trivy import TrivyReport
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.vulnerability import (
    VulnerabilityCreate,
    VulnerabilityRead,
    VulnerabilityUpdate,
)

__all__ = [
    "Severity",
    "VulnerabilityStatus",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "ProjectCreate",
    "ProjectRead",
    "ProjectUpdate",
    "ScanCreate",
    "ScanRead",
    "ScanUpdate",
    "VulnerabilityCreate",
    "VulnerabilityRead",
    "VulnerabilityUpdate",
    "TrivyReport",
]
