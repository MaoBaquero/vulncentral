"""API versionada /api/v1."""

from fastapi import APIRouter

from app.api.v1 import audit_logs, gestores, projects, scans, users, vulnerabilities

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(users.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(vulnerabilities.router)
api_v1_router.include_router(audit_logs.router)
api_v1_router.include_router(gestores.router)

__all__ = ["api_v1_router"]
