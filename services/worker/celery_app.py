"""Aplicación Celery mínima — sin tareas de negocio (Fase 1)."""

from __future__ import annotations

import logging
import os
import sys

from celery import Celery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _broker_url() -> str:
    url = os.getenv("CELERY_BROKER_URL", "").strip()
    if not url:
        raise RuntimeError("CELERY_BROKER_URL no está definida.")
    return url


def _result_backend() -> str | None:
    backend = os.getenv("CELERY_RESULT_BACKEND", "").strip()
    return backend or None


app = Celery(
    "vulncentral",
    broker=_broker_url(),
    backend=_result_backend(),
)

app.conf.update(
    task_default_queue="vulncentral",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

app.autodiscover_tasks(["tasks"], related_name="tasks", force=True)

logger.info("Celery configurado (tarea vulncentral.ingest_trivy_json).")
