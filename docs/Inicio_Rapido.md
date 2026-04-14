# Inicio rápido — VulnCentral

Guía breve para instalar y ejecutar la aplicación. Para detalle técnico adicional, consulta el [README principal](../README.md) del repositorio.

---

## 1. Descarga desde GitHub

### Prerrequisitos

| Requisito | Comprobación sugerida |
|-----------|------------------------|
| **Git** | `git --version` |
| **Docker Engine** y **Docker Compose v2** | `docker --version`, `docker compose version` |
| Espacio en disco y memoria RAM suficientes para varios contenedores (PostgreSQL, RabbitMQ, API, worker, frontend, pgAdmin en desarrollo) | — |
| **Opcional** (solo si desarrollas o pruebas **fuera** de Docker): Python 3.12 (API/tests), Node.js 20 (build local del frontend) | `python --version`, `node --version` |

### Descargar el repositorio

1. Clona el repositorio (HTTPS):

   ```bash
   git clone https://github.com/MaoBaquero/vulncentral.git
   cd vulncentral
   ```

2. (Opcional) Cambia a la rama que quieras desplegar, por ejemplo `main`:

   ```bash
   git checkout main
   git pull
   ```

### Ajustar configuración (obligatorio antes del primer arranque)

1. Crea el archivo de entorno a partir del ejemplo:

   **Linux / macOS / Git Bash**

   ```bash
   cp .env.example .env
   ```

   **Windows PowerShell**

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edita `.env` y sustituye al menos:

   - Contraseñas de **PostgreSQL** (`POSTGRES_PASSWORD`, etc.).
   - **JWT_SECRET** (cadena larga y aleatoria en entornos reales).
   - Credenciales de **RabbitMQ** y coherencia de **`CELERY_BROKER_URL`** con `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS` y `RABBITMQ_DEFAULT_VHOST`.
   - **pgAdmin** (`PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD`) si usas ese servicio.

3. **Frontend y API en el navegador**

   - **`VITE_API_BASE_URL`**: debe ser la URL del API **tal como la ve el navegador** (por defecto `http://localhost:8000` si publicas el API en el puerto 8000 del host).
   - Si cambias **`API_GATEWAY_PORT`** o el host público del API, actualiza también **`VITE_API_BASE_URL`** y **vuelve a construir** el servicio `frontend` (`docker compose build frontend` o `docker compose up --build`).
   - **`CORS_ORIGINS`**: debe incluir el origen exacto desde el que abres el SPA (por ejemplo `http://localhost:8080`).

4. **Base de datos (migraciones Alembic)**

   Tras el primer arranque del stack (o tras actualizar el código con nuevas migraciones), aplica migraciones desde el contenedor del API:

   ```bash
   docker compose exec api-gateway alembic upgrade head
   ```

   Más contexto: [migrations-governance.md](migrations-governance.md).

5. **Solo si vas a contribuir con código**

   El repositorio puede usar `pre-commit` (Semgrep, secret scanning, etc.). No es necesario para “solo usar” la app con Docker. En Windows, si los hooks fallan por codificación, define de forma persistente `PYTHONUTF8=1` y `PYTHONIOENCODING=utf-8` (variables de entorno del usuario) para no tener que prefijarlos en cada `git commit`.

### Construir imágenes y levantar contenedores

**Entorno de desarrollo** (build local de `api-gateway`, `worker` y `frontend`; resto de imágenes desde registro público):

```bash
docker compose up --build
```

En segundo plano:

```bash
docker compose up -d --build
```

**Producción local** (override que reduce exposición de puertos de PostgreSQL y RabbitMQ al host; el frontend queda publicado en **8080:8080** según el override):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up -d --build
```

- **pgAdmin** en el override usa el perfil `dev-tools`: no arranca salvo que ejecutes, por ejemplo:

  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env --profile dev-tools up -d
  ```

Comprueba el estado:

```bash
docker compose ps
```

### Enlaces de conexión (valores por defecto)

Sustituye `localhost` y los puertos si los cambiaste en `.env`.

| Servicio | URL / notas |
|----------|-------------|
| **Frontend (SPA)** | [http://localhost:8080](http://localhost:8080) — puerto del host: variable `FRONTEND_PORT` (por defecto **8080**); dentro del contenedor Nginx escucha en **8080**. |
| **API (salud)** | [http://localhost:8000/health](http://localhost:8000/health) — puerto del host: `API_GATEWAY_PORT` (por defecto **8000**). |
| **RabbitMQ Management** | [http://localhost:15672](http://localhost:15672) — usuario y contraseña según `.env` (`RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`). |
| **pgAdmin** | [http://localhost:5050](http://localhost:5050) — puerto `PGADMIN_PORT` (por defecto **5050**). Al registrar el servidor PostgreSQL en pgAdmin, usa host **`postgres`**, puerto **5432**, y las credenciales de PostgreSQL del `.env`. |

Tras cambiar `FRONTEND_PORT` o `CORS_ORIGINS`, conviene recrear los servicios afectados, por ejemplo:

```bash
docker compose up -d --force-recreate frontend api-gateway
```

### Posibles errores

| Síntoma | Qué revisar |
|---------|-------------|
| **`bind: address already in use`** al publicar puertos | Otro proceso usa el mismo puerto en el host. Cambia `FRONTEND_PORT` / `API_GATEWAY_PORT` en `.env` o libera el puerto. |
| En **PowerShell**, líneas en rojo con `NativeCommandError` junto a mensajes de Docker “Built” | A menudo es **stderr** de Docker, no un fallo real. Verifica con `docker compose ps` que los servicios estén `running` o `healthy`. |
| SPA en blanco o errores de red / CORS | Alinea `CORS_ORIGINS` con la URL real del frontend; revisa `VITE_API_BASE_URL` y reconstruye el `frontend`. |
| API o worker no conectan a la base de datos o a RabbitMQ | Variables en `.env` incoherentes; orden de arranque (`depends_on` + healthchecks). Revisa logs: `docker compose logs api-gateway` (o `worker`, `postgres`, `rabbitmq`). |
| Fallos en **hooks de Git** (Semgrep / encoding) en Windows | Variables persistentes `PYTHONUTF8=1` y `PYTHONIOENCODING=utf-8` (entorno de usuario). |

---

## 2. Descarga desde Docker Hub

La distribución prevista en Docker Hub es **una sola imagen** con el repositorio **`vulncentral`** (nombre del producto **VulnCentral**). La ruta completa en el registro tendrá la forma `docker.io/[USUARIO_O_ORGANIZACIÓN]/vulncentral:[TAG]` (en Docker Hub los nombres de repositorio suelen ir en minúsculas: `vulncentral`).

> **Nota:** Mientras esa imagen no esté publicada, usa la **sección 1** (clon desde GitHub y `docker compose`). El código fuente y los manifiestos actuales ([docker-compose.yml](../docker-compose.yml), [orchestration/docker-swarm/stack.yml](../orchestration/docker-swarm/stack.yml), [orchestration/k8s/](../orchestration/k8s/)) siguen basados en **varios contenedores** por servicio; la imagen única **vulncentral** será el empaquetado publicado para quien instale solo desde el Hub. Los puertos, variables y proceso de arranque exactos dependerán de lo documentado junto al release de esa imagen.

### Prerrequisitos

- **Docker** (`docker pull`, `docker run` o tu orquestador).
- **[COMPLETAR DATO]** — enlace a la página de la imagen en Docker Hub: `https://hub.docker.com/r/[USUARIO_O_ORGANIZACIÓN]/vulncentral` (sustituye el segmento intermedio cuando exista el repositorio público).
- Conocer el **tag** publicado (`latest`, semver, etc.): **[COMPLETAR DATO]** si aún no hay releases fijos.
- Variables de entorno y puertos según la **guía de uso** que acompañe la imagen (equivalente conceptual al `.env` del repositorio: base de datos, broker, JWT, CORS, etc., según cómo esté construida la imagen monolítica o el entrypoint).

### Procedimiento: descargar la imagen

1. Abre en el navegador la ficha de la imagen en Docker Hub: **[COMPLETAR DATO — URL completa del repositorio `.../vulncentral`]**.

2. Copia el comando de pull que muestre Docker Hub, o ejecuta (sustituye organización/usuario y tag):

   ```bash
   docker pull [COMPLETAR_DATO — USUARIO_O_ORG]/vulncentral:[COMPLETAR_TAG]
   ```

   Ejemplo de forma una vez definidos usuario y tag:

   ```bash
   docker pull miorganizacion/vulncentral:latest
   ```

### Comandos de ajuste (si es necesario)

- Crea un archivo de variables o pasa `-e` / `--env-file` según indique la documentación de la imagen publicada.
- Arranque típico (ilustrativo; **ajusta puertos y flags** a lo publicado con la imagen):

  ```bash
  docker run -d --name vulncentral \
    -p [COMPLETAR_PUERTO_HOST_FRONTEND]:[COMPLETAR_PUERTO_CONTENEDOR] \
    -p [COMPLETAR_PUERTO_HOST_API]:[COMPLETAR_PUERTO_CONTENEDOR] \
    --env-file [COMPLETAR_RUTA_AL_.env_OPCIONAL] \
    [COMPLETAR_DATO — USUARIO_O_ORG]/vulncentral:[COMPLETAR_TAG]
  ```

  Si la imagen expone un solo puerto (por ejemplo detrás de un proxy interno), usa un solo `-p` y la documentación del proveedor.

- Para ver logs: `docker logs -f vulncentral`.

### Enlaces de conexión

- Tras el `docker run`, abre en el navegador las URLs que correspondan a los **mapeos `-p`** que hayas usado (por ejemplo `http://localhost:[PUERTO_FRONTEND]` y `http://localhost:[PUERTO_API]/health` si la API sigue expuesta en un puerto distinto).
- Despliegue en servidor o TLS: **[COMPLETAR DATO — URL pública, dominio e ingress]**.

### Posibles errores

| Síntoma | Qué revisar |
|---------|-------------|
| **`pull access denied`** o **manifest unknown** | Usuario/organización, nombre del repo **`vulncentral`** o **tag** incorrectos; imagen aún no publicada o repositorio privado sin `docker login`. |
| **no matching manifest for linux/arm64** (o amd64) | La imagen puede publicarse solo para **linux/amd64** u otra arquitectura; alinea con tu máquina o usa emulación según Docker. |
| El contenedor sale al instante o reinicia en bucle | Revisa `docker logs vulncentral`: variables obligatorias faltantes, conflicto de puertos o error en el entrypoint. |
| La aplicación no responde en el puerto esperado | Los `-p` del host no coinciden con los puertos que escucha el proceso dentro de la imagen; consulta la documentación del release. |
| Errores de base de datos o cola de mensajes | Si la imagen única **no** incluye PostgreSQL/RabbitMQ, debes proporcionar esos servicios y las variables de conexión que exija la imagen. |

---

*Documento alineado con el estado del repositorio en la rama principal. Si cambian puertos o servicios en `docker-compose.yml`, actualiza este archivo en consecuencia.*
