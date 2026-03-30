"""Autenticación JWT, middleware y RBAC."""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.security.password import hash_password


def _login(client: TestClient) -> str:
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "elmero/*-"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_login_ok(client: TestClient) -> None:
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "elmero/*-"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body.get("expires_in", 0) > 0


def test_login_invalid_password(client: TestClient) -> None:
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "wrong"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_me_without_token(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_token"


def test_me_invalid_token(client: TestClient) -> None:
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_token"


def test_me_expired_token(client: TestClient) -> None:
    secret = os.environ["JWT_SECRET"]
    alg = os.getenv("JWT_ALGORITHM", "HS256")
    now = int(time.time())
    token = jwt.encode(
        {"sub": "1", "exp": now - 30, "iat": now - 60},
        secret,
        algorithm=alg,
    )
    if isinstance(token, bytes):
        token = token.decode("ascii")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "token_expired"


def test_me_ok(client: TestClient) -> None:
    token = _login(client)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "elmero@admon.com"
    assert data["role_name"] == "Administrator"


def test_gestor_usuarios_admin_has_read(client: TestClient) -> None:
    token = _login(client)
    r = client.get(
        "/api/gestores/usuarios",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["use_case"] == "Gestor usuarios"


def test_gestor_usuarios_forbidden_for_master(client, engine) -> None:
    """Master no tiene lectura en Gestor usuarios (matriz del seed)."""
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        from sqlalchemy import select

        from app.models.role import Role

        master = db.scalar(select(Role).where(Role.name == "Master"))
        assert master is not None
        u_kwargs: dict[str, Any] = dict(
            name="Master Test",
            email="mastertest@example.com",
            password=hash_password("x"),
            role_id=master.id,
        )
        if db.bind.dialect.name == "sqlite":
            u_kwargs["id"] = 2
        u = User(**u_kwargs)
        db.add(u)
        db.commit()
    finally:
        db.close()

    from app.deps import get_db
    from app.main import create_app

    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        tr = tc.post(
            "/auth/login",
            data={"username": "mastertest@example.com", "password": "x"},
        )
        assert tr.status_code == 200
        token = tr.json()["access_token"]
        r = tc.get(
            "/api/gestores/usuarios",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "forbidden"
    app.dependency_overrides.clear()
