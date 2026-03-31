"""Esquemas Pydantic: Project."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    user_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=50_000)


class ProjectUpdate(BaseModel):
    user_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=50_000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
