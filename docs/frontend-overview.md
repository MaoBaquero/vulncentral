# VulnCentral Frontend

## 🧩 Descripción

**Frontend** de VulnCentral: aplicación **SPA** generada con **Vite** y servida en contenedor mediante **Nginx** (Alpine). Proporciona la interfaz web que consume la **API Gateway**; la URL base de la API se fija en **tiempo de build** (`VITE_API_BASE_URL`), no en tiempo de ejecución del contenedor. Expone el puerto **8080** dentro de la imagen y un endpoint de salud para orquestación.

## 🚀 Características principales

- **Node.js 20** (Alpine) en etapa de build; **Nginx 1.27** (Alpine) en imagen final.
- Build **multi-stage**: `npm ci` + `npm run build`, artefactos estáticos en `/usr/share/nginx/html`.
- **Usuario no root** (`nginx`) en la capa final.
- **Healthcheck** HTTP integrado en el Dockerfile (`/health`).
- Imagen orientada a despliegue detrás de proxy o balanceador; CORS y auth siguen reglas del API Gateway.

## 🏗️ Arquitectura / Rol en el sistema

- **Cliente del API Gateway:** el navegador llama a la API usando la URL incrustada en el bundle en el momento del `docker build` (variable `VITE_API_BASE_URL`).
- **No** incluye backend ni base de datos; depende de un despliegue separado del stack VulnCentral (o de una API accesible desde el cliente).
- En **Docker Compose** del repositorio, el servicio `frontend` depende del healthcheck del `api-gateway`.

## ⚙️ Variables de entorno

### Tiempo de build (imagen Docker)

| Variable / build-arg | Descripción | Requerido | Default |
|----------------------|-------------|-----------|---------|
| `VITE_API_BASE_URL` | URL pública de la API tal como la debe resolver el **navegador** (esquema + host + puerto si aplica). Se inyecta en `docker build` (`ARG`/`ENV` en el Dockerfile). | No (pero necesaria para entornos distintos de localhost) | `http://localhost:8000` |

Cambiar la API tras construir la imagen **no** actualiza el SPA: hace falta **reconstruir** la imagen con otro `VITE_API_BASE_URL`, usar otra tag publicada, o servir el front desde un origen que recompile el proyecto.

### Tiempo de ejecución (contenedor Nginx)

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| — | La imagen publicada no documenta variables de entorno obligatorias para Nginx en el Dockerfile del repositorio. | — | — |

Opcionalmente, en orquestadores se pueden montar fragmentos de configuración Nginx; eso queda fuera del contrato mínimo del repositorio.

## 📦 Uso básico

```bash
docker run --rm -p 8080:8080 \
  maurobaquero/vulncentral-frontend:latest
```

Asegúrate de que la imagen se construyó con un `VITE_API_BASE_URL` alcanzable **desde el navegador** de tus usuarios (p. ej. `https://api.midominio.com`). Para generar una imagen personalizada en local:

```bash
docker build -t mi-frontend:v1 \
  --build-arg VITE_API_BASE_URL=https://api.midominio.com \
  -f services/frontend/Dockerfile services/frontend
```

El flujo de publicación en Hub puede usar una variable de GitHub Actions; véase [DockerHubPL.md](DockerHubPL.md).

## 🔒 Seguridad

- Proceso Nginx bajo **usuario no root** en la imagen final.
- **Trivy** en CI sobre la imagen del frontend (`.github/workflows/ci.yml`).
- No almacena secretos en el bundle si no se inyectan en build; evitar incrustar tokens en `VITE_*`.

## 📈 Observabilidad (si aplica)

- **Healthcheck:** petición HTTP a `http://127.0.0.1:8080/health` (definido en Dockerfile).
- Logs estándar de **Nginx** en stdout/stderr.
- **Métricas Prometheus:** no especificado.

## 🧪 Estado

- **Nivel de madurez (dev / staging / prod):** No especificado en el repositorio.
- **Última actualización esperada en Docker Hub:** No especificado (publicación según [DockerHubPL.md](DockerHubPL.md)).
