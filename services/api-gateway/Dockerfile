FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

RUN mkdir -p /app/data/reports && chown -R appuser:appgroup /app/data

COPY packages/vulncentral-db /opt/vulncentral-db
RUN pip install --upgrade pip && pip install /opt/vulncentral-db

COPY services/api-gateway/requirements.txt .
RUN pip install -r requirements.txt

COPY services/api-gateway/alembic.ini .
COPY services/api-gateway/alembic ./alembic
COPY services/api-gateway/app ./app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
