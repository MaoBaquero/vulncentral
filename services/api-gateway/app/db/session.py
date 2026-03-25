"""Motor SQLAlchemy y fábrica de sesiones."""

from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    """URL de conexión: `DATABASE_URL` o construida desde variables `POSTGRES_*`."""
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    user = os.getenv("POSTGRES_USER", "vulncentral")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "vulncentral")
    password_q = quote_plus(password)
    return f"postgresql+psycopg://{user}:{password_q}@{host}:{port}/{db}"


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)
