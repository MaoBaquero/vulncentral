"""Listado audit_logs /api/v1/audit-logs."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _admin_token(client: TestClient) -> str:
    r = client.post(
        "/auth/login",
        data={"username": "elmero@admon.com", "password": "elmero/*-"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def test_audit_logs_ok(client: TestClient) -> None:
    token = _admin_token(client)
    r = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert body["skip"] == 0
    assert body["limit"] == 50
    assert isinstance(body["items"], list)


def test_audit_logs_pagination(client: TestClient) -> None:
    token = _admin_token(client)
    r = client.get(
        "/api/v1/audit-logs?skip=0&limit=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["limit"] == 10


def test_audit_logs_forbidden_without_token(client: TestClient) -> None:
    r = client.get("/api/v1/audit-logs")
    assert r.status_code == 401
