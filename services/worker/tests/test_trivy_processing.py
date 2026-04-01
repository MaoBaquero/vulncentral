"""Pruebas de rutas, JSON y ciclo de borrado del informe (worker)."""

from __future__ import annotations

import json

import pytest

import db_session
import trivy_processing
from trivy_processing import (
    load_and_validate_report,
    process_report_at_path,
    resolve_safe_report_path,
)


def test_resolve_accepts_file_under_base(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_BASE_DIR", str(tmp_path))
    f = tmp_path / "x.json"
    f.write_text("{}", encoding="utf-8")
    r = resolve_safe_report_path(str(f))
    assert r == str(f.resolve())


def test_resolve_rejects_file_outside_base(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_BASE_DIR", str(tmp_path))
    outside = tmp_path.parent / "secret.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="informe"):
        resolve_safe_report_path(str(outside))


def test_load_and_validate_minimal_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_BASE_DIR", str(tmp_path))
    f = tmp_path / "t.json"
    body = {
        "SchemaVersion": 2,
        "Results": [
            {
                "Target": "Dockerfile",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-1",
                        "PkgName": "openssl",
                        "Severity": "HIGH",
                        "Title": "T",
                    }
                ],
            }
        ],
    }
    f.write_text(json.dumps(body), encoding="utf-8")
    rep = load_and_validate_report(str(f))
    assert len(rep.Results) == 1
    assert rep.Results[0].Vulnerabilities[0].PkgName == "openssl"


def test_process_report_at_path_removes_file_after_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REPORTS_BASE_DIR", str(tmp_path))
    p = tmp_path / "rep.json"
    p.write_text('{"Results":[]}', encoding="utf-8")

    class FakeSess:
        def rollback(self) -> None:
            pass

        def close(self) -> None:
            pass

    monkeypatch.setattr(db_session, "SessionLocal", lambda: FakeSess())
    monkeypatch.setattr(
        trivy_processing,
        "ingest_trivy_report_file",
        lambda db, scan_id, report: 0,
    )

    out = process_report_at_path(1, str(p))
    assert out["vulnerabilities_inserted"] == 0
    assert not p.exists()
