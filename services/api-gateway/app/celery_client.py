"""Cliente Celery mínimo para publicar tareas (sin worker en este proceso)."""

from __future__ import annotations

import os

from celery import Celery

# Mismo nombre que en services/worker/tasks/tasks.py (TASK_NAME_INGEST_TRIVY).
TASK_INGEST_TRIVY_JSON = "vulncentral.ingest_trivy_json"


def _broker_url() -> str:
    url = os.getenv("CELERY_BROKER_URL", "").strip()
    if not url:
        raise RuntimeError("CELERY_BROKER_URL no está definida.")
    return url


celery_app = Celery("vulncentral", broker=_broker_url(), include=[])
celery_app.conf.task_default_queue = "vulncentral"
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]


def enqueue_ingest_trivy_json(
    scan_id: int,
    file_path: str,
    correlation_id: str | None = None,
):
    """Encola procesamiento de informe Trivy (contrato AMQP v1: scan_id, file_path, correlation_id)."""
    args = [scan_id, file_path, correlation_id]
    return celery_app.send_task(
        TASK_INGEST_TRIVY_JSON,
        args=args,
        queue="vulncentral",
    )
