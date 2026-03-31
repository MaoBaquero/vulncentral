"""Enums serializables a JSON (str + Enum)."""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VulnerabilityStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    MITIGATED = "MITIGATED"
    ACCEPTED = "ACCEPTED"
