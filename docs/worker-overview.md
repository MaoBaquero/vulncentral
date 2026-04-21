# VulnCentral Ingestion Worker

## 🧩 Descripción

**Worker** de ingestión de VulnCentral: proceso **Celery** que consume tareas de la cola **RabbitMQ** (cola `vulncentral`), procesa informes **Trivy** en JSON y persiste resultados en **PostgreSQL** usando el mismo esquema de conexión que el API Gateway. Valida rutas de ficheros bajo un directorio base configurable (`REPORTS_BASE_DIR`) para evitar accesos fuera del volumen compartido. No expone HTTP; se opera como worker en segundo plano.

## 🚀 Características principales

- **Celery** con broker AMQP y **result backend** opcional (`CELERY_RESULT_BACKEND`).
- **Python 3.12**, imagen `python:3.12-slim-bookworm`, build **multi-stage** y usuario **no root** (`appuser`).
- **SQLAlchemy** + PostgreSQL (misma lógica de URL que el API: `DATABASE_URL` o `POSTGRES_*`).
- Tarea registrada **`vulncentral.ingest_trivy_json`** (ingesta asíncrona alineada con el contrato del monorepo).
- Concurrencia del worker definida en el Dockerfile de referencia (`--concurrency=2`).

## 🏗️ Arquitectura / Rol en el sistema

- **RabbitMQ:** consumo de tareas publicadas por el **API Gateway** (y potencialmente otros productores compatibles con el mismo contrato AMQP).
- **PostgreSQL:** lectura/actualización de escaneos y vulnerabilidades asociadas al informe Trivy.
- **Sistema de archivos:** lee ficheros JSON bajo `REPORTS_BASE_DIR`; debe coincidir con el volumen donde el API escribe los informes antes de encolar.
- **API Gateway:** no se comunica por HTTP con el worker; el acoplamiento es por **cola** y **rutas de fichero** acordadas.

## ⚙️ Variables de entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `DATABASE_URL` | URL SQLAlchemy completa. Si está definida, tiene prioridad sobre `POSTGRES_*`. | No | (vacío; se construye desde `POSTGRES_*`) |
| `POSTGRES_USER` | Usuario de PostgreSQL. | No | `vulncentral` |
| `POSTGRES_PASSWORD` | Contraseña. | Sí en producción | `""` |
| `POSTGRES_HOST` | Hostname de PostgreSQL. | No | `localhost` |
| `POSTGRES_PORT` | Puerto PostgreSQL. | No | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos. | No | `vulncentral` |
| `CELERY_BROKER_URL` | URL del broker AMQP. | Sí (arranque falla si falta) | — |
| `CELERY_RESULT_BACKEND` | Backend de resultados Celery (p. ej. `rpc://`). | No | `None` (sin backend si vacío) |
| `REPORTS_BASE_DIR` | Directorio base permitido para resolver rutas de informes Trivy de forma segura. | No | `/app/data/reports` |

## 📦 Uso básico

El worker debe ejecutarse en una red donde **RabbitMQ** y **PostgreSQL** sean alcanzables, con el volumen de informes montado en la ruta esperada.

```bash
docker run --rm \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_USER=vulncentral \
  -e POSTGRES_PASSWORD=*** \
  -e POSTGRES_DB=vulncentral \
  -e CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672/vhost \
  -e CELERY_RESULT_BACKEND=rpc:// \
  -v vulncentral_reports:/app/data/reports \
  maurobaquero/vulncentral-worker:latest
```

En la práctica, **`docker compose`** del repositorio mantiene dependencias, healthchecks y volúmenes coherentes; véase el [README principal](../README.md).

## 🔒 Seguridad

- Ejecución como **usuario no root** en la imagen publicada.
- **Normalización de rutas** respecto a `REPORTS_BASE_DIR` para limitar lectura de informes al volumen acordado (código en `trivy_processing.py`).
- **Trivy** en CI sobre la imagen construida del worker (`.github/workflows/ci.yml`).
- Credenciales de base de datos y broker solo por **variables de entorno** o secretos del orquestador.

## 📈 Observabilidad (si aplica)

- Logs Celery en **stdout** (configuración estándar en `celery_app.py`).
- Healthcheck típico en Compose: **`celery inspect ping`** contra la app Celery.
- **Métricas Prometheus / APM:** no especificado en el código actual.

## 🧪 Estado

- **Nivel de madurez (dev / staging / prod):** No especificado en el repositorio.
- **Última actualización esperada en Docker Hub:** No especificado (publicación según [DockerHubPL.md](DockerHubPL.md)).
