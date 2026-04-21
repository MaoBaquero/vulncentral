# VulnCentral API Gateway

## 🧩 Descripción

**API Gateway** de VulnCentral: servicio HTTP principal basado en **FastAPI** y **Uvicorn**. Expone la API REST (`/api/v1`), autenticación JWT, control de acceso y endpoints de salud. Orquesta la persistencia en **PostgreSQL**, publica tareas asíncronas en **RabbitMQ/Celery** (p. ej. ingesta de informes Trivy) y escribe informes JSON en un directorio configurable (`REPORTS_DIR`). Forma parte del monorepo VulnCentral junto al worker de ingestión y el frontend SPA.

## 🚀 Características principales

- **FastAPI** con documentación OpenAPI (`/docs`, `/redoc`).
- **Python 3.12** sobre imagen `python:3.12-slim-bookworm`; build multi-stage con dependencias en venv.
- **SQLAlchemy** + **PostgreSQL** (`psycopg`); URL vía `DATABASE_URL` o variables `POSTGRES_*`.
- **JWT** (HS256 por defecto) para sesiones; **rate limiting** en login (slowapi), configurable por entorno.
- **Celery** como cliente de broker para encolar tareas (sin ejecutar el worker en este contenedor).
- **CORS** configurable para el SPA y desarrollo local.
- **Límite de tamaño** del cuerpo JSON en la ruta de subida de informes Trivy.
- Imagen final con **usuario no root** (`appuser`).

## 🏗️ Arquitectura / Rol en el sistema

- **Entrada** HTTP en el puerto **8000** (típico en contenedor).
- **PostgreSQL:** lectura/escritura de modelos de negocio (usuarios, proyectos, escaneos, vulnerabilidades, auditoría).
- **RabbitMQ:** publicación de tareas Celery (cola `vulncentral`; tarea `vulncentral.ingest_trivy_json` consumida por el **worker**).
- **Sistema de archivos:** escritura de informes Trivy bajo `REPORTS_DIR` (en Compose suele montarse un volumen compartido con el worker).
- **Frontend:** no se sirve desde este servicio; el navegador llama a la API según CORS y la URL configurada en el build del SPA.

## ⚙️ Variables de entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `DATABASE_URL` | URL SQLAlchemy completa (`postgresql+psycopg://...`). Si está definida, **tiene prioridad** sobre `POSTGRES_*`. | No | (vacío; se usa construcción desde `POSTGRES_*`) |
| `POSTGRES_USER` | Usuario de la base de datos. | No | `vulncentral` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL. | Sí en producción | `""` |
| `POSTGRES_HOST` | Hostname del servidor PostgreSQL. | No | `localhost` |
| `POSTGRES_PORT` | Puerto PostgreSQL. | No | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos. | No | `vulncentral` |
| `JWT_SECRET` | Secreto para firmar y verificar JWT. | Sí (arranque falla si falta) | — |
| `JWT_ALGORITHM` | Algoritmo JWT. | No | `HS256` |
| `JWT_EXPIRE_MINUTES` | Duración del access token en minutos (mínimo efectivo 1 min en segundos). | No | `30` |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma. | No | Lista localhost (8080, 80, 5173) si está vacío |
| `CELERY_BROKER_URL` | URL del broker AMQP (RabbitMQ). | Sí (arranque falla si falta) | — |
| `REPORTS_DIR` | Directorio donde la API escribe informes Trivy antes de encolar. | No | `/app/data/reports` |
| `RATE_LIMIT_ENABLED` | Activa rate limiting (`false`/`0`/`off` desactiva). | No | `true` |
| `RATE_LIMIT_LOGIN` | Límite slowapi para login (p. ej. `5/minute`). | No | `5/minute` |
| `MAX_JSON_BODY_BYTES` | Tamaño máximo del cuerpo JSON para `POST .../trivy-report` (bytes). | No | `10485760` (10 MiB) |

**Nota:** En `docker-compose.yml` aparece `CELERY_RESULT_BACKEND` en el servicio api-gateway; el código del API Gateway **no** la lee (el cliente Celery mínimo solo usa el broker). Puede omitirse o mantenerse por homogeneidad con otros servicios.

## 📦 Uso básico

Ejemplo mínimo (asume red Docker y servicios `postgres` y `rabbitmq` alcanzables por nombre o IP; ajusta valores):

```bash
docker run --rm -p 8000:8000 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_USER=vulncentral \
  -e POSTGRES_PASSWORD=*** \
  -e POSTGRES_DB=vulncentral \
  -e JWT_SECRET=*** \
  -e CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672/vhost \
  -v vulncentral_reports:/app/data/reports \
  maurobaquero/vulncentral-api-gateway:latest
```

Para desarrollo local con dependencias ya definidas, suele preferirse **`docker compose`** según el [README principal](../README.md).

## 🔒 Seguridad

- Contenedor ejecuta la aplicación como **usuario no root** (Dockerfile).
- **JWT** obligatorio para rutas protegidas; secreto solo por variable de entorno o secret manager (no commitear).
- **Rate limiting** en login para mitigar fuerza bruta (configurable).
- En el repositorio, las imágenes construidas para este servicio se analizan con **Trivy** en CI (`.github/workflows/ci.yml`, job de imágenes).
- **Gitleaks** y otros hooks en pre-commit reducen filtración de secretos en el código fuente.

## 📈 Observabilidad (si aplica)

- Endpoint **`GET /health`** (usado en healthcheck de Docker Compose).
- Logs en **stdout** con formato estándar (nivel INFO en `main.py`).
- **Métricas tipo Prometheus:** no especificado en el código actual del servicio.

## 🧪 Estado

- **Nivel de madurez (dev / staging / prod):** No especificado en el repositorio.
- **Última actualización esperada en Docker Hub:** No especificado (sigue la cadencia de tags y pushes documentada en [DockerHubPL.md](DockerHubPL.md)).
