"""
Normalización Trivy → vulnerabilities. Modelos canónicos: paquete `vulncentral_db`.
Coherente con `app/api/v1/scans.py` (ingesta asíncrona).
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vulncentral_db.models.scan import Scan
from vulncentral_db.models.vulnerability import Vulnerability
from trivy_schema import TrivyReport

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VulnerabilityStatus(str, Enum):
    OPEN = "OPEN"


def _sanitize_text(value: str | None, *, escape_html: bool = True) -> str | None:
    if value is None:
        return None
    s = value.strip()
    if not s:
        return s
    s = re.sub(r"\s+", " ", s)
    if escape_html:
        return html.escape(s, quote=True)
    return s


def _map_trivy_severity(raw: str | None) -> Severity:
    if not raw:
        return Severity.MEDIUM
    u = raw.strip().upper()
    if u == "UNKNOWN":
        return Severity.LOW
    try:
        return Severity(u)
    except ValueError:
        return Severity.MEDIUM


def _truncate(s: str, max_len: int) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..." if max_len > 3 else s[:max_len]


def _file_path_for_row(pkg: str | None, target: str) -> str:
    pkg_s = (pkg or "").strip()
    tgt = (target or ".").strip() or "."
    if pkg_s and tgt and tgt != ".":
        raw = f"{pkg_s} @ {tgt}"
    elif pkg_s:
        raw = pkg_s
    else:
        raw = tgt
    return _truncate(_sanitize_text(raw, escape_html=False) or ".", 255)


def reports_base_dir() -> str:
    return os.path.normpath(os.path.abspath(os.getenv("REPORTS_BASE_DIR", "/app/data/reports")))


def resolve_safe_report_path(file_path: str) -> str:
    """Devuelve ruta real del fichero o lanza ValueError si no está bajo REPORTS_BASE_DIR."""
    base = reports_base_dir()
    if not os.path.isdir(base):
        raise ValueError(f"Directorio de informes inexistente: {base}")
    abs_requested = os.path.abspath(file_path)
    real_file = os.path.realpath(abs_requested)
    real_base = os.path.realpath(base)
    try:
        common = os.path.commonpath([real_file, real_base])
    except ValueError:
        raise ValueError("Ruta de informe inválida.") from None
    if common != real_base:
        raise ValueError("El informe debe estar bajo el directorio de reportes configurado.")
    if not os.path.isfile(real_file):
        raise ValueError("El fichero de informe no existe o no es un archivo.")
    if not os.access(real_file, os.R_OK):
        raise ValueError("El fichero de informe no es legible.")
    return real_file


def load_and_validate_report(path: str) -> TrivyReport:
    with open(path, encoding="utf-8") as f:
        raw: Any = json.load(f)
    return TrivyReport.model_validate(raw)


def ingest_trivy_report_file(db: Session, scan_id: int, report: TrivyReport) -> int:
    """
    Soft-delete vulnerabilidades activas del scan e inserta filas desde el informe.
    Retorna número de vulnerabilidades insertadas.
    """
    scan = db.scalar(
        select(Scan).where(Scan.id == scan_id, Scan.deleted_at.is_(None)),
    )
    if scan is None:
        raise ValueError(f"Escaneo {scan_id} no encontrado o eliminado.")

    now = datetime.now(timezone.utc)
    existing = db.scalars(
        select(Vulnerability).where(
            Vulnerability.scan_id == scan_id,
            Vulnerability.deleted_at.is_(None),
        ),
    ).all()
    for v in existing:
        v.deleted_at = now

    default_status = VulnerabilityStatus.OPEN.value
    count = 0
    for result in report.Results:
        target = (result.Target or ".").strip() or "."
        for tv in result.Vulnerabilities:
            vid = (tv.VulnerabilityID or "").strip() or "UNKNOWN"
            cve = _truncate(vid, 50)
            title_src = (tv.Title or tv.VulnerabilityID or tv.PkgName or "Finding").strip()
            title = _truncate(_sanitize_text(title_src, escape_html=True) or "Finding", 255)
            desc_raw = tv.Description
            desc = None
            if desc_raw:
                desc = _sanitize_text(desc_raw, escape_html=True)
            sev = _map_trivy_severity(tv.Severity)
            fp = _file_path_for_row(tv.PkgName, target)
            v = Vulnerability(
                scan_id=scan_id,
                title=title,
                description=desc,
                severity=sev.value,
                status=default_status,
                cve=cve,
                file_path=fp,
                line_number=0,
            )
            db.add(v)
            count += 1
    db.commit()
    return count


def process_report_at_path(scan_id: int, file_path: str) -> dict[str, Any]:
    """
    Valida ruta, parsea JSON, persiste en DB y borra el fichero tras commit exitoso.
    """
    safe_path = resolve_safe_report_path(file_path)
    try:
        report = load_and_validate_report(safe_path)
    except Exception as e:
        logger.exception("Error parseando informe Trivy en %s", safe_path)
        raise

    from db_session import SessionLocal

    db = SessionLocal()
    try:
        n = ingest_trivy_report_file(db, scan_id, report)
    except Exception:
        db.rollback()
        logger.exception("Error persistiendo informe para scan_id=%s", scan_id)
        raise
    finally:
        db.close()

    try:
        os.remove(safe_path)
        logger.info("Informe procesado y eliminado: %s (%d vulnerabilidades)", safe_path, n)
    except OSError as e:
        logger.error("No se pudo eliminar el informe tras éxito en DB: %s — %s", safe_path, e)

    return {"scan_id": scan_id, "vulnerabilities_inserted": n}
