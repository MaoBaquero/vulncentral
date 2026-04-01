"""App de prueba con SQLite en memoria, seed y overrides de dependencias."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET", "test-jwt-secret-do-not-use-in-production")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
# Broker en memoria para importar app.celery_client en tests sin RabbitMQ.
os.environ.setdefault("CELERY_BROKER_URL", "memory://")

from app.db.base import Base  # noqa: E402
from app.deps import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.scripts.seed import run_seed  # noqa: E402

import app.models  # noqa: E402, F401


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _sqlite_pragma(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def client(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    s = TestingSessionLocal()
    run_seed(s)
    s.commit()
    s.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
