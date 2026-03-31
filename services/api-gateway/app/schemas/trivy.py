"""Subconjunto flexible del informe JSON de Trivy (validación de entrada)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TrivyCVSS(BaseModel):
    model_config = {"extra": "ignore"}

    V2Vector: str | None = None
    V3Vector: str | None = None


class TrivyVulnerabilityItem(BaseModel):
    """Una vulnerabilidad dentro de `Results[].Vulnerabilities[]`."""

    model_config = {"extra": "ignore"}

    VulnerabilityID: str | None = None
    PkgName: str | None = None
    InstalledVersion: str | None = None
    Severity: str | None = None
    Title: str | None = None
    Description: str | None = None
    PrimaryURL: str | None = None
    CVSS: dict[str, Any] | None = None


class TrivyResult(BaseModel):
    model_config = {"extra": "ignore"}

    Target: str | None = None
    Class: str | None = None
    Type: str | None = None
    Vulnerabilities: list[TrivyVulnerabilityItem] = Field(default_factory=list)


class TrivyReport(BaseModel):
    """Raíz del informe Trivy (schema v2 habitual)."""

    model_config = {"extra": "ignore"}

    SchemaVersion: int | None = None
    ArtifactName: str | None = None
    ArtifactType: str | None = None
    Results: list[TrivyResult] = Field(default_factory=list)
