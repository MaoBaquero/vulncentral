#!/usr/bin/env bash
# Humo: Postgres + RabbitMQ + Core API + Ingestion worker (requiere Docker Compose v2).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
docker compose --env-file "${ENV_FILE:-.env}" up -d postgres rabbitmq api-gateway worker
docker compose --env-file "${ENV_FILE:-.env}" exec -T worker celery -A celery_app inspect ping -t 10
curl -fsS "http://127.0.0.1:${API_GATEWAY_PORT:-8000}/health" >/dev/null
echo "smoke-compose: OK"
