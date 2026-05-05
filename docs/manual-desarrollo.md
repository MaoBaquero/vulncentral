# Manual de Desarrollo — VulnCentral

**Versión:** 1.0
**Proyecto:** VulnCentral — Plataforma DevSecOps
**Institución:** Fundación Universitaria UNIMINUTO
**Autores:** Ing. Argel Ochoa Ronald David · Ing. Baquero Soto Mauricio · Ing. Buitrago Guiot Óscar Javier · Ing. Estefanía Naranjo Novoa

---

## 1. Clonar el Repositorio y Configurar el Entorno Local

![Flujo de configuración del entorno local](../IMG/diagrama-setup-entorno.png)

### 1.1 Prerrequisitos

| Herramienta | Verificación | Versión mínima | Obligatorio |
|-------------|-------------|----------------|-------------|
| Git | `git --version` | cualquier versión | Sí |
| Docker Engine | `docker --version` | 20.10+ | Sí |
| Docker Compose v2 | `docker compose version` | 2.0+ | Sí |
| Python | `python --version` | 3.12 | Solo desarrollo fuera de Docker |
| Node.js | `node --version` | 20 | Solo build local del frontend |
| RAM disponible | — | 4 GB (8 GB recomendado) | Sí |

> **Windows:** si los hooks de pre-commit fallan por encoding, define estas variables de entorno de forma persistente antes de continuar:
> ```powershell
> [System.Environment]::SetEnvironmentVariable("PYTHONUTF8","1","User")
> [System.Environment]::SetEnvironmentVariable("PYTHONIOENCODING","utf-8","User")
> ```

---

### 1.2 Clonar el repositorio

```bash
git clone https://github.com/MaoBaquero/vulncentral.git
cd vulncentral

# Verificar que estás en la rama correcta
git checkout main
git pull
```

---

### 1.3 Configurar variables de entorno

**Linux / macOS / Git Bash:**
```bash
cp .env.example .env
```

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

Edita `.env` y actualiza **obligatoriamente** los siguientes valores antes del primer arranque:

```env
# ── PostgreSQL ──────────────────────────────────────────
POSTGRES_USER=vulncentral
POSTGRES_PASSWORD=CAMBIA_ESTO_POR_UNA_CLAVE_SEGURA
POSTGRES_DB=vulncentral

# ── RabbitMQ (debe coincidir con CELERY_BROKER_URL) ─────
RABBITMQ_DEFAULT_USER=vulncentral
RABBITMQ_DEFAULT_PASS=CAMBIA_ESTO_POR_UNA_CLAVE_SEGURA
RABBITMQ_DEFAULT_VHOST=vulncentral
CELERY_BROKER_URL=amqp://vulncentral:CAMBIA_ESTO@rabbitmq:5672/vulncentral
CELERY_RESULT_BACKEND=rpc://

# ── JWT ─────────────────────────────────────────────────
JWT_SECRET=CADENA_ALEATORIA_LARGA_MINIMO_32_CARACTERES
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ── API y CORS ──────────────────────────────────────────
CORS_ORIGINS=http://localhost:8080
API_GATEWAY_PORT=8000

# ── Frontend ────────────────────────────────────────────
VITE_API_BASE_URL=http://localhost:8000
FRONTEND_PORT=8080

# ── pgAdmin (solo desarrollo) ───────────────────────────
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=CAMBIA_ESTO
```

> Si cambias `API_GATEWAY_PORT` o `FRONTEND_PORT`, actualiza también `VITE_API_BASE_URL` y `CORS_ORIGINS` en consecuencia, y reconstruye el servicio `frontend`.

---

### 1.4 Instalar hooks de pre-commit

Los hooks replican exactamente los controles de seguridad del pipeline CI/CD, ejecutándose localmente en cada `git commit`.

```bash
pip install pre-commit
pre-commit install
```

Hooks instalados (definidos en `.pre-commit-config.yaml`):

| Hook | Versión | Propósito |
|------|---------|-----------|
| `gitleaks` | v8.24.2 | Detecta secretos y credenciales en el código |
| `semgrep` | v1.156.0 | Análisis estático con reglas `p/python` y `p/ci` |
| `bandit` | 1.8.3 | SAST sobre `services/api-gateway` y `services/worker` |
| `pip-audit` | v2.9.0 | CVEs en `requirements.txt` de api-gateway y worker |
| `npm-audit` | sistema | Vulnerabilidades críticas en dependencias del frontend |

```bash
# Ejecutar todos los hooks manualmente (sin necesidad de commit)
pre-commit run --all-files

# Ejecutar un hook específico
pre-commit run gitleaks --all-files
pre-commit run bandit --all-files
```

---

## 2. Ejecutar los Servicios en Modo Desarrollo

### 2.1 Levantar el stack completo

```bash
# Construir imágenes y levantar todos los servicios en segundo plano
docker compose up --build -d

# Verificar el estado de los contenedores (esperar que todos sean "healthy")
docker compose ps
```

Estado esperado al estar listos todos los servicios:

```
NAME                          STATUS
vulncentral-postgres          healthy
vulncentral-rabbitmq          healthy
vulncentral-core-api          healthy
vulncentral-ingestion-worker  healthy
vulncentral-frontend          healthy
vulncentral-pgadmin           healthy
```

---

### 2.2 Aplicar migraciones de base de datos

```bash
# Obligatorio en el primer arranque y tras cada git pull con nuevas migraciones
docker compose exec api-gateway alembic upgrade head
```

> **Regla de gobierno:** solo existe un hilo de migraciones Alembic, ubicado en `services/api-gateway/alembic`. No crear carpetas de migración adicionales en el worker. Ver `docs/migrations-governance.md`.

---

### 2.3 URLs de acceso en desarrollo

| Servicio | URL | Notas |
|----------|-----|-------|
| Frontend SPA | http://localhost:8080 | Puerto configurable con `FRONTEND_PORT` |
| API Gateway | http://localhost:8000 | Puerto configurable con `API_GATEWAY_PORT` |
| Swagger UI | http://localhost:8000/docs | Documentación interactiva de la API |
| ReDoc | http://localhost:8000/redoc | Documentación alternativa de la API |
| Health check | http://localhost:8000/health | Responde `{"status":"ok"}` cuando está listo |
| RabbitMQ Management | http://localhost:15672 | Usuario/pass: valores `RABBITMQ_*` del `.env` |
| pgAdmin | http://localhost:5050 | Usuario/pass: valores `PGADMIN_*` del `.env` |

> En pgAdmin, al registrar el servidor PostgreSQL usa **host: `postgres`**, **puerto: `5432`** y las credenciales `POSTGRES_*` del `.env` (no `localhost`).

---

### 2.4 Comandos útiles durante el desarrollo

```bash
# Ver logs en tiempo real
docker compose logs -f api-gateway
docker compose logs -f worker
docker compose logs -f frontend

# Reiniciar un servicio específico sin reconstruir
docker compose restart api-gateway

# Reconstruir y reiniciar un servicio tras cambios de código
docker compose up --build --force-recreate api-gateway -d

# Abrir una shell dentro de un contenedor
docker compose exec api-gateway bash
docker compose exec worker bash

# Escalar workers horizontalmente
docker compose up --scale worker=3 -d

# Detener todo el stack
docker compose down

# Detener y eliminar volúmenes (⚠️ elimina datos persistidos)
docker compose down -v
```

---

### 2.5 Estructura del proyecto

```
vulncentral/
├── services/
│   ├── api-gateway/        # FastAPI — Core API
│   │   ├── app/
│   │   │   ├── api/        # Rutas y endpoints
│   │   │   ├── middleware/  # JWT, CORS
│   │   │   ├── rbac.py     # Control de acceso por rol
│   │   │   └── security/   # JWT tokens, hashing
│   │   └── alembic/        # Migraciones de BD (único hilo)
│   ├── worker/             # Celery — Ingestion Worker
│   │   ├── tasks/          # Tareas Celery
│   │   └── trivy_processing.py
│   └── frontend/           # React + Vite + Nginx
│       └── src/
│           ├── context/    # AuthContext, RBAC
│           └── pages/
├── packages/
│   └── vulncentral-db/     # Paquete ORM compartido (SQLAlchemy)
├── docs/                   # Documentación técnica
├── docker-compose.yml
├── .env.example
└── .pre-commit-config.yaml
```

---

## 3. Correr las Pruebas Unitarias e Integración

### 3.1 Pruebas del API Gateway (pytest)

```bash
# Ejecutar todas las pruebas dentro del contenedor
docker compose exec api-gateway pytest

# Con reporte de cobertura
docker compose exec api-gateway pytest --cov=app --cov-report=term-missing

# Generar reporte XML (para CI)
docker compose exec api-gateway pytest --cov=app --cov-report=xml

# Ejecutar solo un módulo o test específico
docker compose exec api-gateway pytest tests/test_auth.py
docker compose exec api-gateway pytest tests/test_auth.py::test_login_success -v

# Ejecutar con output detallado
docker compose exec api-gateway pytest -v --tb=short
```

---

### 3.2 Pruebas del Worker (pytest)

```bash
docker compose exec worker pytest

# Con cobertura
docker compose exec worker pytest --cov=tasks --cov=trivy_processing --cov-report=term-missing
```

---

### 3.3 Pruebas del Frontend (npm)

```bash
docker compose exec frontend npm test

# En modo watch (desarrollo activo)
docker compose exec frontend npm run test:watch

# Generar reporte de cobertura
docker compose exec frontend npm run test:coverage
```

---

### 3.4 Análisis de seguridad estático (SAST)

```bash
# Bandit sobre el código Python
docker compose exec api-gateway bandit -r app/ -lll -q

# Semgrep con reglas Python y CI
semgrep scan --config p/python --config p/ci services/api-gateway services/worker --severity ERROR

# Gitleaks — detección de secretos
gitleaks detect --source . --verbose

# pip-audit — CVEs en dependencias Python
pip-audit -r services/api-gateway/requirements.txt
pip-audit -r services/worker/requirements.txt

# npm audit — CVEs en dependencias frontend
npm audit --audit-level=critical --prefix services/frontend
```

---

### 3.5 Prueba DAST con OWASP ZAP

```bash
# ZAP Baseline contra el entorno de desarrollo levantado
docker run --network vulncentral_net owasp/zap2docker-stable \
  zap-baseline.py -t http://api-gateway:8000 -r zap-report.html
```

---

### 3.6 Cobertura mínima requerida

| Servicio | Cobertura mínima | Comando |
|----------|-----------------|---------|
| `api-gateway` | 85% | `pytest --cov=app --cov-fail-under=85` |
| `worker` | 80% | `pytest --cov=tasks --cov-fail-under=80` |

---

## 4. Contribuir al Proyecto

### 4.1 Branching Strategy

![Branching Strategy — VulnCentral](../IMG/diagrama-branching-strategy.png)


El proyecto sigue **GitHub Flow** adaptado con rama `develop` como capa de integración:

| Rama | Propósito | Quién escribe | Merge hacia |
|------|-----------|---------------|-------------|
| `main` | Código en producción. Protegida. | CI/CD únicamente | — |
| `develop` | Integración continua. Base de trabajo diario. | PRs desde feature/* | `main` (releases) |
| `feature/<nombre>` | Nueva funcionalidad o mejora | Desarrollador | `develop` vía PR |
| `fix/<descripcion>` | Corrección de bug no crítico | Desarrollador | `develop` vía PR |
| `hotfix/<descripcion>` | Corrección urgente en producción | Desarrollador | `main` y `develop` |

**Flujo estándar para una nueva feature:**

```bash
# 1. Partir siempre desde develop actualizado
git checkout develop
git pull origin develop

# 2. Crear rama de feature
git checkout -b feature/nombre-descriptivo

# 3. Desarrollar y commitear (ver convención de commits)
git add .
git commit -m "feat(api): agregar endpoint de resumen de vulnerabilidades"

# 4. Mantener la rama actualizada con develop
git fetch origin
git rebase origin/develop

# 5. Abrir Pull Request hacia develop
# — en GitHub: base: develop, compare: feature/nombre-descriptivo
```

**Flujo para un hotfix:**

```bash
# 1. Partir desde main
git checkout main
git pull origin main
git checkout -b hotfix/descripcion-breve

# 2. Aplicar la corrección y commitear
git commit -m "fix(auth): corregir validación de token expirado"

# 3. Merge a main Y a develop
git checkout main && git merge hotfix/descripcion-breve
git checkout develop && git merge hotfix/descripcion-breve
git push origin main develop
git branch -d hotfix/descripcion-breve
```

---

### 4.2 Convención de Commits (Conventional Commits)

El proyecto usa **Conventional Commits v1.0.0**. El formato es:

```
<tipo>(<alcance>): <descripción corta en imperativo>

[cuerpo opcional — explica el QUÉ y el POR QUÉ, no el cómo]

[pie opcional — referencias a issues, breaking changes]
```

**Tipos válidos:**

| Tipo | Cuándo usarlo | Ejemplo |
|------|--------------|---------|
| `feat` | Nueva funcionalidad | `feat(api): agregar filtro por severidad CVE` |
| `fix` | Corrección de bug | `fix(worker): reintentos al fallar conexión DB` |
| `docs` | Solo documentación | `docs(readme): actualizar instrucciones de instalación` |
| `test` | Agregar o corregir tests | `test(auth): cubrir caso de token expirado` |
| `refactor` | Refactoring sin cambio funcional | `refactor(rbac): simplificar lógica de permisos` |
| `chore` | Tareas de mantenimiento | `chore(deps): actualizar FastAPI a 0.110` |
| `ci` | Cambios en pipeline CI/CD | `ci: agregar job de escaneo Trivy` |
| `security` | Parche de seguridad | `security(jwt): rotar algoritmo de firma` |

**Alcances comunes:** `api`, `worker`, `frontend`, `db`, `auth`, `rbac`, `ci`, `docker`

**Ejemplos correctos:**

```bash
git commit -m "feat(worker): implementar soft-delete de vulnerabilidades previas al reprocesar"
git commit -m "fix(auth): slowapi rate limit no aplica en entorno de pruebas"
git commit -m "test(api): agregar tests de integración para endpoint trivy-report"
git commit -m "chore(docker): reducir imagen api-gateway de 1.2GB a 480MB con multi-stage build"
```

**Breaking changes** — se indican con `!` o en el pie:

```bash
git commit -m "feat(api)!: cambiar esquema de respuesta de /vulnerabilities

BREAKING CHANGE: el campo 'severity_level' renombrado a 'severity'.
Actualizar clientes que consuman este endpoint."
```

---

### 4.3 Pipeline CI/CD — Proceso Automático

![Pipeline CI/CD DevSecOps](../IMG/diagrama-pipeline-cicd.png)

Cada `push` o `pull_request` hacia `develop` o `main` dispara automáticamente el pipeline en GitHub Actions:

```
push / PR
    │
    ▼
[job: security]          ← falla → PR bloqueado
  Bandit (SAST Python)
  Semgrep (análisis estático)
  Gitleaks (secretos)
  pip-audit (CVEs Python)
    │
    ▼
[job: build]             ← falla en CVE HIGH/CRIT → bloqueado
  docker build
  trivy image scan
  push al registro
    │
    ▼
[job: test]              ← cobertura < 85% → bloqueado
  pytest + coverage
  ZAP baseline (DAST)
    │
    ▼
[deploy staging]         ← solo si todos los jobs pasan
```

---

### 4.4 Proceso de Revisión de Pull Requests

**Antes de abrir el PR:**

```bash
# 1. Verificar que todos los hooks pasan localmente
pre-commit run --all-files

# 2. Asegurarse de que las pruebas pasan
docker compose exec api-gateway pytest --cov=app

# 3. Actualizar la rama con develop
git rebase origin/develop

# 4. Verificar que no hay secretos ni credenciales
gitleaks detect --source . --verbose
```

**Checklist del PR — debe cumplirse todo antes del merge:**

- [ ] El título sigue la convención de commits (`tipo(alcance): descripción`)
- [ ] La descripción explica el propósito y los cambios principales
- [ ] Todos los jobs del pipeline CI/CD pasan (verde)
- [ ] La cobertura de pruebas no decreció
- [ ] Si toca tablas `vulnerabilities` o `scans`, se revisó con el equipo de worker y API
- [ ] Si hay migración de BD, se probó `alembic upgrade head` y `alembic downgrade -1`
- [ ] Se actualizó la documentación afectada (`docs/`)
- [ ] Al menos **1 reviewer** aprobó el PR

**Reglas de merge:**

| Rama destino | Método de merge | Quién puede mergear |
|--------------|----------------|---------------------|
| `develop` | Squash and merge | Cualquier miembro con aprobación |
| `main` | Merge commit | Solo maintainers (release) |

---

### 4.5 Consideraciones especiales para migraciones de base de datos

```bash
# Crear una nueva migración (dentro del contenedor api-gateway)
docker compose exec api-gateway alembic revision --autogenerate -m "descripcion_del_cambio"

# Revisar el script generado antes de aplicar
# Archivo en: services/api-gateway/alembic/versions/

# Aplicar la migración
docker compose exec api-gateway alembic upgrade head

# Revertir la última migración (si algo falla)
docker compose exec api-gateway alembic downgrade -1

# Ver historial de migraciones
docker compose exec api-gateway alembic history --verbose
```

> **Regla crítica:** si una migración modifica `vulnerabilities` o `scans` (tablas escritas por API y Worker), el PR debe mencionarlo explícitamente y probar ambos servicios. Desplegar API y Worker en la misma ventana cuando el cambio rompe compatibilidad con versiones anteriores.

---

## Referencias

| Documento | Descripción |
|-----------|-------------|
| [`docs/migrations-governance.md`](./migrations-governance.md) | Gobierno de migraciones Alembic |
| [`docs/amqp-ingest-contract.md`](./amqp-ingest-contract.md) | Contrato AMQP del worker de ingesta |
| [`docs/architecture-shared-db-microservices.md`](./architecture-shared-db-microservices.md) | Arquitectura de BD compartida y matriz de tablas |
| [`docs/requerimientos_cloud.md`](./requerimientos_cloud.md) | Requerimientos para despliegue en nube |
| [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Definición de hooks de seguridad locales |

---

*Versión 1.0 — VulnCentral · UNIMINUTO · Especialización en Ciberseguridad*
