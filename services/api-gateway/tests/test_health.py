"""Pruebas mínimas del endpoint de salud."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_service_name() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body.get("service") == "vulncentral-api-gateway"
