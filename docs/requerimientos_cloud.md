# Requerimientos técnicos para despliegue en la nube (VulnCentral)

Documento orientado a planificar el despliegue de **VulnCentral** en un proveedor cloud genérico (IaaS, PaaS o Kubernetes), alineado con la arquitectura descrita en el README: **frontend (SPA + Nginx)**, **API Gateway (FastAPI)**, **worker (Celery)**, **PostgreSQL**, **RabbitMQ** y **almacenamiento compartido** para informes JSON antes de la ingesta.

---

## 1. Cómputo y contenedores

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| C1 | Motor de contenedores o equivalente (Docker en VM, Kubernetes, ECS, Cloud Run con multi-container, etc.) | Sí | El repo se entrega con `Dockerfile` por servicio y `docker-compose.yml`. |
| C2 | Capacidad de ejecutar **al menos 5 procesos** (Postgres, RabbitMQ, API, worker, frontend) o su equivalente gestionado | Sí | En `docker-compose.prod.yml` los límites de memoria orientativos suman del orden de **~3 GiB** (Postgres 1 G, Rabbit 768 M, API 512 M, worker 512 M, frontend 256 M). El plan real debe incluir **RAM y CPU** suficientes más overhead del SO/orquestador. |
| C3 | Imágenes construibles desde el repositorio (`services/api-gateway`, `services/worker`, `services/frontend`; contexto raíz donde aplique) | Sí | Coherente con los `build.context` del compose. |
| C4 | Política de **reinicio** (restart) o salud del orquestador | Recomendado | `docker-compose.prod.yml` usa `restart: always` en servicios críticos. |
| C5 | **Health checks** HTTP para API y frontend; comprobaciones para Postgres, RabbitMQ y Celery según el entorno | Recomendado | El compose de desarrollo define healthchecks; en cloud conviene equivalentes para despliegues sin downtime. |

---

## 2. Red y exposición

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| N1 | **Tráfico HTTPS** desde el navegador hacia el frontend (y preferiblemente hacia el API) | Sí (producción) | TLS vía balanceador, proxy inverso o certificados gestionados (ACM, Let’s Encrypt, etc.). |
| N2 | URL pública o accesible para el **SPA** y para el **API** (mismo dominio con rutas o subdominios) | Sí | El frontend se construye con `VITE_API_BASE_URL` apuntando a la URL que ve el **navegador**. |
| N3 | **CORS**: variable `CORS_ORIGINS` debe incluir el origen exacto del front (esquema + host + puerto si aplica) | Sí | Ver `.env.example`. |
| N4 | Reglas de **firewall / security groups**: exponer solo puertos necesarios (p. ej. 443/80); **no** publicar Postgres (5432) ni AMQP (5672) a Internet | Sí | Alineado con `docker-compose.prod.yml` (sin mapeo de puertos de Postgres/Rabbit al host). |
| N5 | Conectividad **privada** entre API, worker, Postgres y RabbitMQ (misma VPC, red de contenedores, mesh, etc.) | Sí | Los servicios deben resolverse por hostname interno (equivalente a nombres de servicio en Compose). |
| N6 | Opcional: acceso restringido a **RabbitMQ Management** (15672) solo por VPN/bastion | Opcional | Solo si se expone la UI de gestión. |

---

## 3. Datos: PostgreSQL

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| D1 | **PostgreSQL** compatible con SQLAlchemy/psycopg (versión acorde a la imagen del proyecto, p. ej. 16 en compose) | Sí | Variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, host/puerto o `DATABASE_URL`. |
| D2 | Persistencia durable (volumen, disco gestionado, RDS, etc.) | Sí | |
| D3 | Estrategia de **migraciones** (Alembic u otra) ejecutable en el entorno de despliegue | Sí | El paquete compartido `packages/vulncentral-db` y el flujo de despliegue deben aplicar esquema actualizado. |
| D4 | Copias de seguridad y restauración (RPO/RTO según política) | Recomendado | Especialmente si el despliegue deja de ser solo académico. |

---

## 4. Mensajería: RabbitMQ (Celery)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| M1 | **RabbitMQ** accesible por AMQP desde API y worker | Sí | `CELERY_BROKER_URL` (p. ej. `amqp://user:pass@host:5672/vhost`). Usuario, contraseña y vhost coherentes con `RABBITMQ_*`. |
| M2 | Backend de resultados Celery (`CELERY_RESULT_BACKEND`, p. ej. `rpc://` en desarrollo) | Sí | En producción avanzada puede evaluarse Redis/DB; el proyecto documenta `rpc://` para desarrollo. |
| M3 | Persistencia de colas/datos de broker si se requiere sobrevivir a reinicios | Recomendado | Volumen o servicio gestionado con persistencia. |

---

## 5. Almacenamiento compartido (informes Trivy)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| S1 | **Almacenamiento compartido** entre API y worker bajo la misma ruta lógica (p. ej. `/app/data/reports`) o mecanismo equivalente | Sí * | El API escribe JSON; el worker lee y elimina tras commit. En Compose: volumen `reports_data`. En PaaS sin volumen compartido entre servicios hace falta **diseño alternativo** (objeto, DB, cola con payload, etc.). |
| S2 | Límite de tamaño de cuerpo JSON configurable (`MAX_JSON_BODY_BYTES`, por defecto 10 MiB) | Recomendado | Proxies/load balancers deben permitir al menos ese tamaño en `POST .../trivy-report`. |

\*Obligatorio para el flujo de ingesta Trivy tal como está implementado en el repositorio.

---

## 6. Secretos y configuración

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| K1 | Gestión segura de secretos: `POSTGRES_PASSWORD`, `RABBITMQ_DEFAULT_PASS`, `JWT_SECRET`, credenciales AMQP | Sí | Preferible almacén de secretos del proveedor o variables cifradas; no commitear `.env`. |
| K2 | `JWT_SECRET` fuerte y rotación según política | Sí | Autenticación JWT (Fase 3). |
| K3 | `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` acordes con el cliente | Sí | Valores por defecto en `.env.example`. |
| K4 | Rate limiting (`RATE_LIMIT_ENABLED`, `RATE_LIMIT_LOGIN`) si se expone login públicamente | Recomendado | Ver `.env.example`. |

---

## 7. Build del frontend

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| F1 | **Node.js** (p. ej. 20) para `npm ci` / `npm run build` en pipeline o imagen | Sí | README indica Node 20 para build local. |
| F2 | Inyección en **build-time** de `VITE_API_BASE_URL` con la URL pública del API | Sí | Vite embebe la variable en el bundle estático. |
| F3 | Servir el artefacto estático con **Nginx** (imagen del repo) o CDN/static hosting equivalente | Sí | |

---

## 8. CI/CD y calidad (alineado con objetivos DevSecOps del proyecto)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| P1 | Pipeline que construya imágenes o artefactos y despliegue al entorno cloud | Recomendado | El README describe GitHub Actions (job `security`, etc.). |
| P2 | Escaneo de secretos, dependencias y linters en CI | Recomendado | Ya contemplado en el proyecto académico. |
| P3 | Versionado de imágenes (tags por commit) y trazabilidad | Recomendado | |

---

## 9. Observabilidad y operación

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| O1 | Agregación de **logs** (stdout/stderr de contenedores o equivalente) | Recomendado | |
| O2 | Endpoint de salud del API (`/health`) monitorizable | Recomendado | Usado en healthcheck del compose. |
| O3 | Alertas de facturación y cuotas (en cloud público) | Recomendado | Evita sobrecostes en proyectos académicos. |

---

## 10. Resumen de variables de entorno relevantes

| Variable (ejemplo) | Servicios típicos | Uso |
|--------------------|-------------------|-----|
| `POSTGRES_*` / `DATABASE_URL` | API, worker | Conexión a BD |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | API, worker | Cola Celery |
| `JWT_*` | API | Autenticación |
| `CORS_ORIGINS` | API | CORS del SPA |
| `VITE_API_BASE_URL` | Build frontend | Base URL del API en el navegador |
| `RATE_LIMIT_*`, `MAX_JSON_BODY_BYTES` | API | Límites y tamaño de cuerpo |
| `REPORTS_DIR` / `REPORTS_BASE_DIR` | API, worker | Rutas de informes (volumen compartido) |

Referencia completa: `.env.example` en la raíz del repositorio.

---

## Referencias en el repositorio

- Arquitectura y flujo de ingesta: `README.md`, `docs/architecture-shared-db-microservices.md`
- Orquestación local y producción: `docker-compose.yml`, `docker-compose.prod.yml`
- Manifiestos de ejemplo: `orchestration/k8s/`, `orchestration/docker-swarm/`
