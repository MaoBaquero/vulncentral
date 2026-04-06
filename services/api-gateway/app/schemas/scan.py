"""Esquemas Pydantic: Scan."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScanCreate(BaseModel):
    project_id: int
    tool: str = Field(..., min_length=1, max_length=255)
    status: str = Field(..., min_length=1, max_length=50)


class ScanUpdate(BaseModel):
    project_id: int | None = None
    tool: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = Field(None, min_length=1, max_length=50)


class ScanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: str | None = None
    tool: str
    status: str
    created_at: datetime
    updated_at: datetime
