# Requerimientos técnicos para despliegue en la nube (VulnCentral)

Documento orientado a planificar el despliegue de **VulnCentral** en un proveedor cloud genérico (IaaS, PaaS o Kubernetes), alineado con la arquitectura del README: **frontend (SPA + Nginx)**, **API Gateway (FastAPI)**, **worker (Celery)**, más **PostgreSQL**, **RabbitMQ** y **almacenamiento compartido** para informes JSON antes de la ingesta.

En `docker-compose.yml` aparecen **seis** servicios (`postgres`, `pgadmin`, `rabbitmq`, `api-gateway`, `worker`, `frontend`). En un despliegue de producción típico **solo tres** son cargas de trabajo que el equipo construye y opera como contenedores o jobs propios:

| Rol | Servicio en Compose | En producción optimizada |
|-----|---------------------|---------------------------|
| API | `api-gateway` | Contenedor / PaaS / pod propio |
| Worker | `worker` | Contenedor / PaaS / pod propio |
| Frontend | `frontend` | Contenedor / static hosting propio |

Los otros tres se cubren con **servicios gestionados** (o equivalente del proveedor), sin levantar esos contenedores en el clúster:

| Rol | Servicio en Compose | En producción optimizada |
|-----|---------------------|---------------------------|
| Base de datos | `postgres` | PostgreSQL gestionado (RDS, Cloud SQL, Azure Database for PostgreSQL, etc.) |
| Cola AMQP | `rabbitmq` | Broker gestionado compatible AMQP (Amazon MQ for RabbitMQ, CloudAMQP, etc.) o alternativa acordada con el código Celery |
| Consola SQL (solo desarrollo) | `pgadmin` | **No** es requisito de producción; sustituir por consola del proveedor, cliente SQL vía VPN, o perfil `dev-tools` solo en entornos no productivos |

El cómputo y los health checks de las secciones siguientes se centran en esos **tres** despliegues propios; el dimensionamiento de BD y broker es un **SKU aparte** en el catálogo del proveedor.

---

## 1. Cómputo y contenedores

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| C1 | Motor de contenedores o equivalente (Docker en VM, Kubernetes, ECS, Cloud Run con multi-container, etc.) | Sí | El repo se entrega con `Dockerfile` por servicio y `docker-compose.yml`. |
| C2 | Capacidad de ejecutar **al menos 3 procesos** de aplicación (API, worker, frontend) o su equivalente (p. ej. front en CDN y solo API+worker en contenedores) | Sí | Con los límites orientativos de `docker-compose.prod.yml` solo para esos tres servicios, la suma de memoria límite es del orden de **~1,25 GiB** (API 512 M, worker 512 M, frontend 256 M). El plan debe sumar **RAM y CPU** suficientes más overhead del SO u orquestador. La base PostgreSQL y RabbitMQ gestionados tienen su propia facturación y tamaño de instancia; no entran en ese ~1,25 GiB. |
| C3 | Imágenes construibles desde el repositorio (`services/api-gateway`, `services/worker`, `services/frontend`; contexto raíz donde aplique) | Sí | Coherente con los `build.context` del compose. |
| C4 | Política de **reinicio** (restart) o salud del orquestador | Recomendado | `docker-compose.prod.yml` usa `restart: always` en servicios críticos. |
| C5 | **Health checks** HTTP para API y frontend; comprobaciones para Celery en el worker según el entorno | Recomendado | El compose de desarrollo define healthchecks para API y front; el worker usa `celery inspect ping`. En cloud conviene equivalentes para despliegues sin downtime. Las comprobaciones de Postgres y RabbitMQ en compose no aplican si son servicios gestionados: el proveedor expone métricas o health del servicio. |

---

## 2. Red y exposición

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| N1 | **Tráfico HTTPS** desde el navegador hacia el frontend (y preferiblemente hacia el API) | Sí (producción) | TLS vía balanceador, proxy inverso o certificados gestionados (ACM, Let’s Encrypt, etc.). |
| N2 | URL pública o accesible para el **SPA** y para el **API** (mismo dominio con rutas o subdominios) | Sí | El frontend se construye con `VITE_API_BASE_URL` apuntando a la URL que ve el **navegador**. |
| N3 | **CORS**: variable `CORS_ORIGINS` debe incluir el origen exacto del front (esquema + host + puerto si aplica) | Sí | Ver `.env.example`. |
| N4 | Reglas de **firewall / security groups**: exponer solo puertos necesarios (p. ej. 443/80 hacia API y front); **no** publicar a Internet los endpoints de Postgres ni AMQP del servicio gestionado (o restringirlos a redes privadas/VPC) | Sí | Aunque la BD y el broker no corran en tus VMs, sus hostnames suelen ser alcanzables por red; debe aplicarse el principio de menor exposición. |
| N5 | Conectividad **privada o lista de permitidos** desde API y worker hacia el **hostname** del PostgreSQL gestionado y del **broker AMQP** (VPC peering, Private Link, subredes autorizadas, etc.) | Sí | Equivalente a que en Compose todos compartan `vulncentral_net`. |
| N6 | Opcional: UI de administración del broker (tipo RabbitMQ Management en 15672) solo por VPN/bastion si el proveedor la expone | Opcional | Depende del producto gestionado elegido. |

---

## 3. Datos: PostgreSQL (gestionado recomendado)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| D1 | **PostgreSQL** compatible con SQLAlchemy/psycopg (versión acorde al proyecto, p. ej. 16 en compose de referencia) | Sí | Variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, host/puerto o `DATABASE_URL`. En servicio gestionado: usuario/clave del proveedor, SSL si lo exige el endpoint. |
| D2 | Persistencia durable gestionada por el proveedor (discos, réplicas, PITR según el tier) | Sí | Sustituye al volumen `postgres_data` del compose. |
| D3 | Estrategia de **migraciones** (Alembic u otra) ejecutable contra ese endpoint (p. ej. job de despliegue o pipeline con red a la BD) | Sí | El paquete `packages/vulncentral-db` y el flujo de despliegue deben aplicar esquema actualizado. |
| D4 | Copias de seguridad y restauración (RPO/RTO según política) | Recomendado | En BD gestionada suele venir del plan del proveedor; documentar responsabilidad y pruebas de restore. |

---

## 4. Mensajería: RabbitMQ / AMQP (gestionado recomendado)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| M1 | **Broker AMQP** accesible desde API y worker (compatible con la URL de `CELERY_BROKER_URL`) | Sí | P. ej. `amqp://user:pass@host:5672/vhost`. Con RabbitMQ gestionado, usuario, contraseña y vhost los define el proveedor. |
| M2 | Backend de resultados Celery (`CELERY_RESULT_BACKEND`, p. ej. `rpc://` en desarrollo) | Sí | En producción avanzada puede evaluarse Redis/DB; el proyecto documenta `rpc://` para desarrollo. |
| M3 | Persistencia y disponibilidad del broker según política de colas | Recomendado | En servicio gestionado: elegir tier con persistencia y HA si el negocio lo requiere. |

---

## 5. Almacenamiento compartido (informes Trivy)

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| S1 | **Almacenamiento compartido** entre API y worker bajo la misma ruta lógica (p. ej. `/app/data/reports`) o mecanismo equivalente | Sí * | El API escribe JSON; el worker lee y elimina tras commit. En Compose: volumen `reports_data`. En cloud: volumen compartido del orquestador, NFS, EFS, Azure Files, etc. Si el PaaS no permite volumen compartido entre réplicas, hace falta **diseño alternativo** (objeto, DB, cola con payload, etc.). |
| S2 | Límite de tamaño de cuerpo JSON configurable (`MAX_JSON_BODY_BYTES`, por defecto 10 MiB) | Recomendado | Proxies/load balancers deben permitir al menos ese tamaño en `POST .../trivy-report`. |

\*Obligatorio para el flujo de ingesta Trivy tal como está implementado en el repositorio.

---

## 6. Secretos y configuración

| ID | Requisito | Obligatorio | Notas |
|----|-----------|-------------|--------|
| K1 | Gestión segura de secretos: credenciales de PostgreSQL gestionado, credenciales AMQP, `JWT_SECRET` | Sí | Preferible almacén de secretos del proveedor o variables cifradas; no commitear `.env`. |
| K2 | `JWT_SECRET` fuerte y rotación según política | Sí | Autenticación JWT. |
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
| O1 | Agregación de **logs** (stdout/stderr de API, worker y front) | Recomendado | |
| O2 | Endpoint de salud del API (`/health`) monitorizable | Recomendado | Usado en healthcheck del compose. |
| O3 | Métricas y alertas del **PostgreSQL** y del **broker** según el producto gestionado | Recomendado | Sustituye en parte la observabilidad “por contenedor” de Postgres/Rabbit en compose. |
| O4 | Alertas de facturación y cuotas (en cloud público) | Recomendado | Evita sobrecostes en proyectos académicos. |

---

## 10. Resumen de variables de entorno relevantes

| Variable (ejemplo) | Servicios típicos | Uso |
|--------------------|-------------------|-----|
| `POSTGRES_*` / `DATABASE_URL` | API, worker | Conexión a BD (endpoint del servicio gestionado) |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | API, worker | Cola Celery (endpoint del broker gestionado) |
| `JWT_*` | API | Autenticación |
| `CORS_ORIGINS` | API | CORS del SPA |
| `VITE_API_BASE_URL` | Build frontend | Base URL del API en el navegador |
| `RATE_LIMIT_*`, `MAX_JSON_BODY_BYTES` | API | Límites y tamaño de cuerpo |
| `REPORTS_DIR` / `REPORTS_BASE_DIR` | API, worker | Rutas de informes (volumen compartido o equivalente) |

Referencia completa: `.env.example` en la raíz del repositorio.

---

## 11. Resumen numérico (referencia rápida)

| Concepto | Cantidad / orden de magnitud |
|----------|------------------------------|
| Servicios **desplegados como aplicación** (imágenes propias) | **3** (API, worker, frontend) |
| Dependencias típicas **gestionadas** | **2** obligatorias en producción (PostgreSQL, broker AMQP); **pgAdmin** no cuenta como requisito de producción |
| Memoria límite orientativa solo app (`docker-compose.prod.yml`) | **~1,25 GiB** sumando API + worker + frontend; más overhead de plataforma |

---

## Referencias en el repositorio

- Arquitectura y flujo de ingesta: `README.md`, `docs/architecture-shared-db-microservices.md`
- Orquestación local y producción: `docker-compose.yml`, `docker-compose.prod.yml`
- Manifiestos de ejemplo: `orchestration/k8s/`, `orchestration/docker-swarm/`
