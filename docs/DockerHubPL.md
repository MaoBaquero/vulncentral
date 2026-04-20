# Publicación de imágenes en Docker Hub

Este documento describe el flujo automático de construcción y publicación de las imágenes propias de VulnCentral en Docker Hub, y cómo usarlas después del despliegue en el registro.

## Objetivo

Publicar tres imágenes bajo el namespace **`maurobaquero`** cuando se integra código en la rama **`main`** o cuando se crea un **tag Git** de versión con prefijo `v` (por ejemplo `v1.0.0`).

## Workflow de GitHub Actions

| Campo | Valor |
|--------|--------|
| Archivo | [`.github/workflows/docker-publish.yml`](../.github/workflows/docker-publish.yml) |
| Nombre del workflow | Publish Docker Hub |
| Disparadores | `push` a `main`; `push` de tags que coinciden con `v*` |

El job usa **Docker Buildx**, **caché tipo `gha`** (GitHub Actions cache) y **`docker/build-push-action`** para construir y subir cada imagen.

## Imágenes publicadas

Convención de nombres (fija en el workflow):

| Imagen Docker Hub | Origen en el repo |
|-------------------|-------------------|
| `maurobaquero/vulncentral-api-gateway` | Contexto raíz, `services/api-gateway/Dockerfile` |
| `maurobaquero/vulncentral-worker` | Contexto raíz, `services/worker/Dockerfile` |
| `maurobaquero/vulncentral-frontend` | Contexto `services/frontend`, `Dockerfile` del front |

Plataforma de build en CI: **`linux/amd64`**. Para ARM64 u otras arquitecturas habría que ampliar el workflow (por ejemplo `platforms: linux/amd64,linux/arm64` y emulación QEMU); no está habilitado por defecto.

## Política de tags

| Situación | Tags que se publican (por imagen) |
|-----------|-------------------------------------|
| Push a la rama **`main`** | `latest`, `sha-<commit_corto>` |
| Push de un tag Git **`v*`** (ej. `v1.0.0`) | El nombre exacto del tag (ej. `v1.0.0`) y `sha-<commit_corto>` |

**Importante:** el tag `latest` **solo** se actualiza en pushes a `main`, no al publicar solo un tag de release (salvo que en el futuro se amplíe la política).

## Configuración en GitHub

### Secrets (obligatorios)

En el repositorio: **Settings → Secrets and variables → Actions → Secrets**.

| Secret | Descripción |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Usuario de Docker Hub (puede ser `maurobaquero`). |
| `DOCKERHUB_TOKEN` | Personal Access Token (PAT) de Docker Hub con permiso de **escritura** (Write) sobre repositorios de imágenes; no uses la contraseña de la cuenta. |

Crear el PAT en Docker Hub: **Account settings → Security → New access token**.

### Variables (recomendado para el frontend)

En **Settings → Secrets and variables → Actions → Variables** (pestaña *Variables*):

| Variable | Uso |
|----------|-----|
| `VITE_API_BASE_URL` | URL base de la API que el frontend de Vite debe usar **en tiempo de build** (por ejemplo `https://api.ejemplo.com`). Si se deja vacía o no se define, el workflow usa por defecto `http://localhost:8000` (útil como placeholder hasta definir un entorno real). |

Cada valor distinto de `VITE_API_BASE_URL` genera un **bundle distinto**; en la práctica son **imágenes de frontend distintas** para cada URL. Para varios entornos suele publicarse con tags diferentes (por ejemplo asociados a tags Git `v*`) o con pipelines separados.

## Cómo usar las imágenes publicadas

### Descargar

```bash
docker pull maurobaquero/vulncentral-api-gateway:latest
docker pull maurobaquero/vulncentral-worker:latest
docker pull maurobaquero/vulncentral-frontend:latest
```

Sustituye `latest` por `sha-<hash>` o por un tag de versión (`v1.0.0`) según lo que necesites reproducir.

### Variables de entorno en runtime

Las imágenes **no** sustituyen la configuración de `docker-compose.yml`: siguen necesitando las mismas variables en tiempo de ejecución (PostgreSQL, RabbitMQ, JWT, Celery, etc.) que cuando se construyen en local. Consulta el [README principal](../README.md) y el fichero `.env.example` del repositorio.

Ejemplo mínimo de arranque del API (ilustrativo; ajusta red, secretos y volúmenes a tu entorno):

```bash
docker run --rm -p 8000:8000 \
  -e POSTGRES_HOST=... \
  -e POSTGRES_USER=... \
  -e POSTGRES_PASSWORD=... \
  -e POSTGRES_DB=... \
  maurobaquero/vulncentral-api-gateway:latest
```

El **worker** Celery y el **frontend** se ejecutan de forma análoga con las variables que ya documenta el proyecto para cada servicio.

### Compose

El repositorio sigue orientado a `docker compose build` para desarrollo. Para producción con imágenes de Hub puedes definir en tu propio override de Compose (fuera del alcance del fichero `docker-compose.prod.yml` versionado en este plan) entradas `image: maurobaquero/vulncentral-...` y los mismos `environment` que el servicio equivalente.

## Optimización de contexto de build

El [`.dockerignore`](../.dockerignore) en la raíz del monorepo excluye, entre otros, `.cursor`, `docs` y `services/frontend` para los builds cuyo contexto es la raíz (**api-gateway** y **worker**), reduciendo el contexto enviado al daemon sin afectar a los `COPY` necesarios en esos Dockerfiles.

## Recomendaciones de optimización (Dockerfiles)

- **api-gateway** y **worker**: ya usan multi-stage, `python:3.12-slim-bookworm`, venv copiado a la imagen final y usuario no root; no se aplicaron cambios estructurales adicionales.
- **frontend**: mantiene build con Node 20 Alpine y servido con Nginx; revisar periódicamente versiones base (`node`, `nginx`) por parches de seguridad.
- **Multi-arquitectura**: si necesitas imágenes nativas en ARM (Apple Silicon en Linux, AWS Graviton, etc.), amplía el workflow con `platforms: linux/amd64,linux/arm64` y `docker/setup-qemu-action` antes de Buildx (aumenta tiempo de build).

## Checklist de validación (post-configuración)

1. **Local:** `docker compose build` (o al menos `docker compose build api-gateway worker frontend`) funciona en tu máquina con el código actual.
2. **GitHub:** Secrets `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN` creados en el repositorio (o a nivel de organización, si aplica).
3. **Variable opcional:** `VITE_API_BASE_URL` definida si el frontend publicado debe apuntar a una API concreta (no localhost).
4. **Primera publicación:** hacer `push` a `main` (o crear un tag `v*`) y comprobar en la pestaña **Actions** que el workflow **Publish Docker Hub** termina en verde.
5. **Docker Hub:** comprobar que existen las tres imágenes y los tags esperados (`latest` y/o `sha-...` y/o `v...`).

Si el workflow falla en el login, revisa que el PAT no haya expirado y que el secret se llame exactamente como espera el YAML.

## Referencia cruzada

La especificación funcional del trabajo está alineada con el prompt interno [`.cursor/prompts/Publicacion_Docker_Hub.md`](../.cursor/prompts/Publicacion_Docker_Hub.md).
