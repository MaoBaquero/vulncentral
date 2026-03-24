FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

RUN mkdir -p /app/data/reports && chown -R appuser:appgroup /app/data

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY celery_app.py .
COPY tasks ./tasks

USER appuser

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=2"]
