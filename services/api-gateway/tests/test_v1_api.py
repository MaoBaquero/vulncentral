"""CRUD /api/v1, Trivy y errores HTTP."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.models.role import Role
from app.models.user import User
from app.security.password import hash_password


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "elmero/*-"},
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


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


def test_v1_users_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/users")
    assert r.status_code == 401


def test_v1_users_list_admin(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.get("/api/v1/users", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(u["email"] == "elmero@admon.com" for u in data)


def test_v1_users_master_forbidden(client: TestClient, master_headers: dict[str, str]) -> None:
    r = client.get("/api/v1/users", headers=master_headers)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_v1_create_user_conflict_email(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "name": "Dup",
            "email": "elmero@admon.com",
            "password": "secret123",
        },
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_v1_admin_cannot_create_scan(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/v1/scans",
        headers=admin_headers,
        json={"project_id": 1, "tool": "trivy", "status": "pending"},
    )
    assert r.status_code == 403


def test_v1_project_scan_trivy_flow(
    client: TestClient,
    master_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    pr = client.post(
        "/api/v1/projects",
        headers=master_headers,
        json={"user_id": 1, "name": "Proyecto API", "description": "desc"},
    )
    assert pr.status_code == 201
    project_id = pr.json()["id"]

    sr = client.post(
        "/api/v1/scans",
        headers=master_headers,
        json={"project_id": project_id, "tool": "trivy", "status": "done"},
    )
    assert sr.status_code == 201
    scan_id = sr.json()["id"]

    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))

    _captured: list[tuple[int, str, str | None]] = []

    def _fake_enqueue(sid: int, fp: str, correlation_id: str | None = None):
        class _R:
            id = "test-task-id"

        _captured.append((sid, fp, correlation_id))
        return _R()

    monkeypatch.setattr(
        "app.api.v1.scans.enqueue_ingest_trivy_json",
        _fake_enqueue,
    )

    trivy_body = {
        "SchemaVersion": 2,
        "ArtifactName": "test",
        "Results": [
            {
                "Target": "Dockerfile",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-0001",
                        "Severity": "HIGH",
                        "Title": "Test finding",
                        "Description": "Something",
                    }
                ],
            }
        ],
    }
    tr = client.post(
        f"/api/v1/scans/{scan_id}/trivy-report",
        headers=master_headers,
        json=trivy_body,
    )
    assert tr.status_code == 202
    payload = tr.json()
    assert payload["status"] == "queued"
    assert payload["task_id"] == "test-task-id"
    assert payload["file_path"].endswith(".json")
    assert "correlation_id" in payload and len(payload["correlation_id"]) > 0
    assert len(_captured) == 1
    assert _captured[0][0] == scan_id
    assert _captured[0][1] == payload["file_path"]
    assert _captured[0][2] == payload["correlation_id"]
    assert Path(payload["file_path"]).is_file()


def test_trivy_report_validation_422(
    client: TestClient,
    master_headers: dict[str, str],
    engine,
) -> None:
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        from app.models.project import Project
        from app.models.scan import Scan

        p = Project(user_id=1, name="p", description=None)
        db.add(p)
        db.flush()
        s = Scan(project_id=p.id, tool="t", status="s")
        db.add(s)
        db.commit()
        scan_id = s.id
    finally:
        db.close()

    r = client.post(
        f"/api/v1/scans/{scan_id}/trivy-report",
        headers=master_headers,
        json={"SchemaVersion": "not-an-int"},
    )
    assert r.status_code == 422


def test_trivy_payload_too_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_JSON_BODY_BYTES", "50")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    app = create_app()
    with TestClient(app) as client:
        body = b"{" + b'"x": "' + b"y" * 100 + b'"}'
        r = client.post(
            "/api/v1/scans/1/trivy-report",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 413
        assert r.json()["error"]["code"] == "payload_too_large"


def test_v1_vulnerability_not_found(
    client: TestClient,
    master_headers: dict[str, str],
) -> None:
    r = client.get("/api/v1/vulnerabilities/99999", headers=master_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_v1_create_vulnerability_master(
    client: TestClient,
    master_headers: dict[str, str],
    engine,
) -> None:
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = Session()
    try:
        from app.models.project import Project
        from app.models.scan import Scan

        p = Project(user_id=1, name="pv", description=None)
        db.add(p)
        db.flush()
        s = Scan(project_id=p.id, tool="t", status="s")
        db.add(s)
        db.commit()
        scan_id = s.id
    finally:
        db.close()

    r = client.post(
        "/api/v1/vulnerabilities",
        headers=master_headers,
        json={
            "scan_id": scan_id,
            "title": "XSS",
            "description": "bad",
            "severity": "HIGH",
            "status": "OPEN",
            "cve": "CVE-2023-1",
            "file_path": "app.py",
            "line_number": 10,
        },
    )
    assert r.status_code == 201
    vid = r.json()["id"]

    gr = client.get(f"/api/v1/vulnerabilities/{vid}", headers=master_headers)
    assert gr.status_code == 200
    assert gr.json()["severity"] == "HIGH"
