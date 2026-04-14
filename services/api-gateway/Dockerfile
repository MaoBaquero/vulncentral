# Multi-stage: dependencias en venv; imagen final sin compiladores ni fuentes del paquete db.
FROM python:3.12-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY packages/vulncentral-db /opt/vulncentral-db
RUN pip install --upgrade pip && pip install /opt/vulncentral-db

COPY services/api-gateway/requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Parches de seguridad de Debian (reduce CVEs en capa OS antes de fijar usuario app).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

RUN mkdir -p /app/data/reports && chown -R appuser:appgroup /app/data

COPY services/api-gateway/alembic.ini .
COPY services/api-gateway/alembic ./alembic
COPY services/api-gateway/app ./app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
