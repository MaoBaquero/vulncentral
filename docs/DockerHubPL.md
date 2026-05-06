# Inicio rápido — solo imágenes Docker Hub

Esta guía levanta **todo** VulnCentral usando **únicamente** imágenes publicadas en Docker Hub (`maurobaquero/vulncentral-*`) más PostgreSQL y RabbitMQ oficiales. **No** hace falta construir imágenes en local.

Para desarrollo con `build` desde el código fuente, usa el [`docker-compose.yml`](../docker-compose.yml) del repositorio y la guía [Inicio rápido](Inicio_Rapido.md).

---

## Qué incluye

| Componente | Origen |
|------------|--------|
| API, worker, frontend | Docker Hub (`maurobaquero/vulncentral-api-gateway`, `vulncentral-worker`, `vulncentral-frontend`) |
| Base de datos y cola | Imágenes oficiales `postgres:16-alpine`, `rabbitmq:3.13-management-alpine` |
| Fichero Compose | [`docker-compose.hub.yml`](../docker-compose.hub.yml) en la raíz del repo (autocontenido) |

---

## Prerrequisitos

| Requisito | Comprobación |
|-----------|----------------|
| **Docker Engine** y **Docker Compose v2** | `docker --version`, `docker compose version` |
| **RAM** suficiente para varios contenedores (orientativo: 2–4 GiB libres) | — |
| Puertos libres en el host según tu `.env` (por defecto: **5432** Postgres, **5672**/**15672** RabbitMQ, **8000** API, **8080** frontend) | — |

---

## 🎯 **Ultra Fast Review**
Simplemente sigue en orden los siguientes pasos y podrás realizar la instalación del sistema tipo **NO Verbose**, si requieres información detallada **continua al siguiente literal**.

1. Crear una nueva carpeta (Cualquier nombre), ubíquese dentro de ella a través de una terminal.
2. Copiar en esa carpeta [`docker-compose.hub.yml`](../docker-compose.hub.yml) y [`.env.example`](../.env.example) como plantilla (desde el mismo repositorio).
3. Ejecutar **en orden** los siguientes comandos:

```bash
cp .env.example .env
```
```bash
docker compose -f docker-compose.hub.yml up -d
```
```bash
docker compose -f docker-compose.hub.yml exec api-gateway alembic upgrade head
```
```bash
docker compose -f docker-compose.hub.yml exec api-gateway python -m app.scripts.seed
```

🔥 **¡Listo, tienes instalado VulnCentral!**

4. Entrar a **`http://localhost:8080/login`**. 

```
🧨 Si ves **«Failed to fetch»** o no hay conexión con el API, comprueba **`VITE_API_BASE_URL`** y **`CORS_ORIGINS`** en `.env`, reinicia el frontend con `docker compose -f docker-compose.hub.yml up -d frontend` y revisa la sección **ADVERTENCIA: URL del API en el navegador** más abajo (la URL del API para el navegador la toma el contenedor desde `.env`; la imagen Hub debe incluir `/config.json` generado al arrancar).
```

### Primera conexión al aplicativo

```
elmero@admon.com 
elmero/*-
```

## PASOS DE INSTALACIÓN DETALLADOS

### 1. Obtener el Compose y el ejemplo de entorno

- **Opción A:** clona el repositorio y trabaja en la carpeta raíz.
- **Opción B:** descarga solo [`docker-compose.hub.yml`](../docker-compose.hub.yml) y copia también [`.env.example`](../.env.example) como plantilla (desde el mismo repositorio).

### 2. Crear el archivo `.env`

```bash
cp .env.example .env
```

Edita `.env` y **cambia al menos**:

- Contraseñas de **PostgreSQL** (`POSTGRES_PASSWORD`, etc.).
- **JWT_SECRET** (cadena larga y aleatoria en entornos reales).
- Credenciales **RabbitMQ** y coherencia de **`CELERY_BROKER_URL`** y **`CELERY_RESULT_BACKEND`** con `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS` y `RABBITMQ_DEFAULT_VHOST` (el host del broker dentro de Compose debe ser **`rabbitmq`**).
- **`CORS_ORIGINS`**: debe incluir el **origen exacto** del SPA en el navegador (p. ej. `http://localhost:8080` si abres el front en ese puerto).

### 3. Elegir tag de las imágenes de aplicación

En `.env` puedes definir:

```env
VULNCENTRAL_TAG=v1.0.0
```

Si no lo defines, el compose usa por defecto **`v1.0.0`**. Otras opciones habituales en Hub: `latest`, `sha-xxxx` (según lo publicado). Las tres imágenes (api-gateway, worker, frontend) deben usar el **mismo** tag para un despliegue coherente.

### 4. Arrancar

Desde el directorio donde están `docker-compose.hub.yml` y `.env`:

```bash
docker compose -f docker-compose.hub.yml up -d
```

La primera vez se harán `pull` de las imágenes; requiere red y puede tardar varios minutos.

### 5. Migraciones (obligatorio tras el primer arranque)

El API **no** aplica migraciones de Alembic al iniciar. Ejecuta:

```bash
docker compose -f docker-compose.hub.yml exec api-gateway alembic upgrade head
```

### 6. Datos iniciales (opcional)

Para cargar roles/usuarios de demostración alineados con el proyecto:

```bash
docker compose -f docker-compose.hub.yml exec api-gateway python -m app.scripts.seed
```

---

## Acceso

| Servicio | URL típica (valores por defecto del `.env.example`) |
|----------|-----------------------------------------------------|
| Frontend (SPA) | `http://localhost:8080` (puerto `FRONTEND_PORT`) |
| API | `http://localhost:8000` (puerto `API_GATEWAY_PORT`) |
| RabbitMQ Management | `http://localhost:15672` (si expusiste el puerto) |

Comprueba el API con: `GET http://localhost:8000/health` (ajusta host/puerto según tu `.env`).

---

## ADVERTENCIA: URL del API en el navegador

En **`docker-compose.hub.yml`**, el servicio **`frontend`** recibe **`VC_API_BASE_URL`** (por defecto el mismo valor que **`VITE_API_BASE_URL`** en tu `.env`). Al arrancar el contenedor se genera **`/config.json`** con la URL pública del API; el SPA la usa en **runtime**, así que puedes cambiar host/puerto **sin reconstruir la imagen** (reinicia solo el contenedor `frontend` tras editar `.env`).

En **`docker-compose.yml`** (build local del front), **`VITE_API_BASE_URL`** sigue siendo el fallback en desarrollo y el valor por defecto del bundle si no hubiera `config.json`.

- **`CORS_ORIGINS`** en el API debe listar el origen exacto del SPA (esquema + host + puerto).

Más detalle: [diagnostico-ingesta-trivy-carga.md](diagnostico-ingesta-trivy-carga.md) (incluye «Failed to fetch» y checklist).

---

## Problemas frecuentes y soluciones

| Síntoma | Causa probable | Qué hacer |
|---------|----------------|-----------|
| `manifest unknown` o error al hacer pull | Tag `VULNCENTRAL_TAG` no existe en Docker Hub | Comprueba tags publicados; prueba `latest` o un `sha-*` existente. |
| API healthy pero login o datos fallan | Migraciones no ejecutadas | `docker compose -f docker-compose.hub.yml exec api-gateway alembic upgrade head` |
| «Failed to fetch» / CORS en el navegador | Origen del SPA no está en `CORS_ORIGINS`, `VITE_API_BASE_URL` / `VC_API_BASE_URL` incorrectos o API caído | Ajusta `.env`, reinicia `api-gateway` y `frontend`; revisa la sección anterior y [diagnostico-ingesta-trivy-carga.md](diagnostico-ingesta-trivy-carga.md). |
| Worker no procesa informes Trivy (202 pero sin datos en BD) | Worker caído, cola o volumen `reports_data` | [diagnostico-ingesta-trivy-carga.md](diagnostico-ingesta-trivy-carga.md): `docker compose ps`, logs del worker, volumen compartido. |
| Celery no conecta | Usuario/clave/vhost en `CELERY_BROKER_URL` no coinciden con `RABBITMQ_*` | Revisa `.env` y reinicia `api-gateway` y `worker`. |

---

## Detener y borrar datos

```bash
docker compose -f docker-compose.hub.yml down -v
```

**`-v`** elimina volúmenes (PostgreSQL, RabbitMQ, informes Trivy en `reports_data`). Úsalo solo si quieres un reset completo.

---

## Validar el fichero Compose

```bash
docker compose -f docker-compose.hub.yml config
```

Debe mostrar la configuración interpolada sin errores.
