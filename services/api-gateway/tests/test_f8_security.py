"""Fase 8: MIME en JSON, auditoría en login, IDOR por rol Inspector."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.security.password import hash_password


@pytest.fixture
def master_headers(client: TestClient, engine) -> dict[str, str]:
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        master = db.scalar(select(Role).where(Role.name == "Master"))
        assert master is not None
        if db.scalar(select(User).where(User.email == "masterapi@example.com")) is None:
            kwargs: dict = dict(
                name="Master API",
                email="masterapi@example.com",
                password=hash_password("mpass"),
                role_id=master.id,
            )
            if db.bind.dialect.name == "sqlite":
                kwargs["id"] = 2
            db.add(User(**kwargs))
            db.commit()
    finally:
        db.close()
    r = client.post(
        "/auth/login",
        data={"username": "masterapi@example.com", "password": "mpass"},
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_trivy_report_rejects_non_json_content_type(
    client: TestClient,
    master_headers: dict[str, str],
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    pr = client.post(
        "/api/v1/projects",
        headers=master_headers,
        json={"user_id": 2, "name": "P MIME", "description": None},
    )
    assert pr.status_code == 201
    pid = pr.json()["id"]
    sr = client.post(
        "/api/v1/scans",
        headers=master_headers,
        json={"project_id": pid, "tool": "trivy", "status": "done"},
    )
    assert sr.status_code == 201
    sid = sr.json()["id"]
    body = b'{"SchemaVersion":2,"Results":[]}'
    r = client.post(
        f"/api/v1/scans/{sid}/trivy-report",
        headers={
            **master_headers,
            "Content-Type": "text/plain",
            "Content-Length": str(len(body)),
        },
        content=body,
    )
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "unsupported_media_type"


def test_login_success_creates_audit_row(client: TestClient, engine) -> None:
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        before = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    finally:
        db.close()
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "elmero/*-"},
    )
    assert r.status_code == 200
    db = Session()
    try:
        after = db.scalar(select(func.count()).select_from(AuditLog)) or 0
        assert after > before
        last = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).first()
        assert last is not None
        assert last.action == "login_success"
        assert last.entity == "auth"
    finally:
        db.close()


def test_inspector_cannot_read_foreign_project(client: TestClient, engine, master_headers) -> None:
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        insp_role = db.scalar(select(Role).where(Role.name == "Inspector"))
        assert insp_role is not None
        u_kwargs: dict[str, Any] = dict(
            name="Inspector IDOR",
            email="inspector-idor@example.com",
            password=hash_password("secret123"),
            role_id=insp_role.id,
        )
        if db.bind.dialect.name == "sqlite":
            u_kwargs["id"] = 99
        db.add(User(**u_kwargs))
        db.commit()
    finally:
        db.close()

    pr = client.post(
        "/api/v1/projects",
        headers=master_headers,
        json={"user_id": 1, "name": "Proyecto ajeno", "description": None},
    )
    assert pr.status_code == 201
    foreign_pid = pr.json()["id"]

    ir = client.post(
        "/auth/login",
        data={"username": "inspector-idor@example.com", "password": "secret123"},
    )
    assert ir.status_code == 200
    itoken = ir.json()["access_token"]
    iheaders = {"Authorization": f"Bearer {itoken}"}
    gr = client.get(f"/api/v1/projects/{foreign_pid}", headers=iheaders)
    assert gr.status_code == 404
