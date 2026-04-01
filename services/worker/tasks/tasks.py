"""Tareas Celery — ingesta asíncrona de informes Trivy (Fase 5)."""

from __future__ import annotations

import json
import logging

from celery_app import app
from pydantic import ValidationError

logger = logging.getLogger(__name__)

TASK_NAME_INGEST_TRIVY = "vulncentral.ingest_trivy_json"


@app.task(name=TASK_NAME_INGEST_TRIVY, bind=True, max_retries=3, default_retry_delay=60)
def ingest_trivy_json(
    self,
    scan_id: int,
    file_path: str,
    correlation_id: str | None = None,
) -> dict:
    """
    Lee un JSON de Trivy desde el volumen compartido, normaliza y guarda en PostgreSQL.
    Args: scan_id, ruta absoluta del fichero, correlation_id opcional (contrato AMQP v1).
    """
    from trivy_processing import process_report_at_path

    extra = {"correlation_id": correlation_id} if correlation_id else {}
    try:
        result = process_report_at_path(scan_id, file_path)
        if correlation_id:
            logger.info("ingest_trivy_json OK scan_id=%s %s", scan_id, extra)
        return result
    except (ValueError, ValidationError, json.JSONDecodeError) as e:
        logger.warning("Informe inválido ingest_trivy_json scan_id=%s: %s %s", scan_id, e, extra)
        raise
    except Exception as exc:
        logger.exception("Fallo ingest_trivy_json scan_id=%s path=%s %s", scan_id, file_path, extra)
        raise self.retry(exc=exc) from exc
