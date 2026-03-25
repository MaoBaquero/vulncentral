# VulnCentral

Plataforma base (Fase 1): estructura de repositorio, Docker Compose, servicios mínimos sin lógica de negocio.

## Requisitos

| Herramienta | Comprobación |
|-------------|--------------|
| Docker Engine + Compose v2 | `docker --version`, `docker compose version` |
| Python 3.12 (tests locales del API) | `python --version` |
| Node.js 20 (build local del frontend) | `node --version` |

## Inicio rápido

1. Copiar variables de entorno:

   ```bash
   cp .env.example .env
   ```

   Edita `.env` y cambia contraseñas y secretos.

2. Levantar el stack en desarrollo:

   ```bash
   docker compose up --build
   ```

3. Comprobar servicios:

   - Frontend: [http://localhost:80](http://localhost:80) (o el puerto mapeado si cambias el compose)
   - API: [http://localhost:8000/health](http://localhost:8000/health) (puerto por defecto `API_GATEWAY_PORT`)
   - RabbitMQ Management: [http://localhost:15672](http://localhost:15672) (usuario/clave según `.env`)
   - pgAdmin: [http://localhost:5050](http://localhost:5050) (puerto `PGADMIN_PORT`; email/clave `PGADMIN_DEFAULT_*` en `.env`). Al registrar el servidor usa host **`postgres`**, puerto **5432**, usuario y contraseña de PostgreSQL del `.env`.

## Producción (override)

Reduce exposición de puertos y ajusta límites:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
```

En el override, el frontend suele publicarse en el host en el puerto **8080** (`8080:80`). PostgreSQL y RabbitMQ dejan de exponer puertos al host; usa red interna o túnel según tu despliegue. **pgAdmin** queda asignado al perfil `dev-tools` y no arranca salvo que ejecutes `docker compose ... --profile dev-tools up`.

## Volúmenes

- **Informes compartidos**: volumen Docker `reports_data` montado en **`/app/data/reports`** en `api-gateway` y `worker`.
- **Datos de PostgreSQL y RabbitMQ**: volúmenes nombrados `postgres_data` y `rabbitmq_data`.

## Límites de memoria (`deploy.resources.limits.memory`)

El `docker-compose.yml` define `deploy.resources.limits.memory` por servicio, como pide la especificación. Con `docker compose up` (sin Swarm), **algunas versiones ignoran la sección `deploy`**; para aplicar límites de forma efectiva puedes usar **Docker Swarm** (`docker stack deploy -c orchestration/docker-swarm/stack.yml vulncentral`, tras construir y publicar imágenes) o definir alternativas compatibles con tu entorno.

## Estructura del repositorio

```text
vulncentral/
├── services/
│   ├── frontend/      # React (Vite) + nginx
│   ├── api-gateway/   # FastAPI
│   └── worker/        # Celery
├── orchestration/     # Docker Swarm, Kubernetes
├── infrastructure/    # Terraform, Ansible
├── monitoring/        # Prometheus, Grafana, Loki (referencia)
├── docs/
└── .github/workflows/
```

## Celery

- **Broker**: RabbitMQ (`CELERY_BROKER_URL`).
- **Resultados (desarrollo)**: `CELERY_RESULT_BACKEND=rpc://` (mismo broker). Para producción avanzada se puede migrar a Redis o base de datos en fases posteriores.

## Kubernetes (esqueleto)

Manifiestos de ejemplo en [`orchestration/k8s/`](orchestration/k8s/). Ajusta [`secrets.yaml`](orchestration/k8s/secrets.yaml) y construye las imágenes `vulncentral/api-gateway`, `vulncentral/worker` y `vulncentral/frontend` antes de aplicar.

Hosts de ejemplo en Ingress: `api.vulncentral.local`, `app.vulncentral.local`.

## Verificación local (sin Docker)

```bash
# API Gateway
cd services/api-gateway
pip install -r requirements-dev.txt
pytest -q

# Frontend
cd services/frontend
npm ci
npm run build
```

## Validar Compose

```bash
docker compose --env-file .env.example config
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.example config
```

## Licencia

Ver [LICENSE](LICENSE).
