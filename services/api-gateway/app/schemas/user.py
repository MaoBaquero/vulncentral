"""Esquemas Pydantic: User."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    role_id: int | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=1, max_length=128)
    role_id: int | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role_id: int | None
    created_at: datetime
    updated_at: datetime
