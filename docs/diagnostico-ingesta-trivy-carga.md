# Diagnóstico: «Cargar» informe Trivy (UI) y persistencia en PostgreSQL

El botón **Cargar** en [VulnerabilitiesPage](../services/frontend/src/pages/VulnerabilitiesPage.jsx) envía el JSON a `POST /api/v1/scans/{scan_id}/trivy-report` (202 + cola Celery). La escritura en base de datos ocurre **solo** cuando el contenedor **`worker`** procesa la tarea `vulncentral.ingest_trivy_json`.

## 1. Comprobar el stack

```bash
docker compose ps
```

Deben estar **healthy** (o al menos *Up*) como mínimo: `postgres`, `rabbitmq`, `api-gateway`, **`worker`**. El volumen **`reports_data`** debe montarse en `/app/data/reports` en **api-gateway** y **worker** (definido en `docker-compose.yml`).

```bash
docker volume inspect vulncentral_reports_data
```

## 2. Logs del worker tras «Encolado»

```bash
docker compose logs worker --tail=80
```

Busca líneas `ingest_trivy_json OK` o `Informe procesado y eliminado`. Si aparece **`ModuleNotFoundError: No module named 'trivy_processing'`** en `ForkPoolWorker`, la imagen del worker debe incluir `PYTHONPATH=/app` (ver [Dockerfile del worker](../services/worker/Dockerfile)). Tras corregir:

```bash
docker compose build worker
docker compose up -d worker
```

## 3. Prueba manual con JSON mínimo

Ejemplo con escaneo `3` (ajusta `scan_id` y el token):

```bash
# Token (sustituye usuario/contraseña)
curl -s -X POST "http://localhost:8000/auth/login" \
  --data-urlencode "username=elmero@admon.com" \
  --data-urlencode "password=TU_CLAVE" | jq -r .access_token
```

```bash
export TOKEN=...
curl -s -w "\nHTTP:%{http_code}\n" \
  -X POST "http://localhost:8000/api/v1/scans/3/trivy-report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @scripts/smoke-trivy-minimal.json
```

Para un informe **amplio** (metadata Trivy, `CVSS` anidado, `References`, etc.), usa el mismo `curl` sustituyendo el fichero por `@scripts/sample-trivy-full-report.json`.

Debe responder **202** y `status: queued`. Tras unos segundos, `GET /api/v1/vulnerabilities` debe incluir filas nuevas para ese `scan_id` con `cve` / `title` del JSON.

**Nota:** un informe con `Results: []` o sin entradas en `Vulnerabilities` encola correctamente pero **inserta 0** filas.

## 4. Causas frecuentes (resumen)

| Síntoma | Causa probable |
|---------|----------------|
| 202 pero nada en BD | `worker` parado, RabbitMQ inaccesible, error en tarea (ver logs) |
| `ModuleNotFoundError: trivy_processing` | Falta `PYTHONPATH=/app` en la imagen del worker (corregido en el Dockerfile del repo) |
| 202 y 0 vulnerabilidades | JSON sin hallazgos en `Results[].Vulnerabilities` |
| No ves filas en la tabla | Filtro por contexto de escaneo en la SPA: abre vulnerabilidades desde el escaneo correcto o quita el filtro implícito |

## 5. «Failed to fetch» al pulsar Enviar (modal Trivy)

Ese mensaje lo genera el **navegador** cuando `fetch()` no obtiene una respuesta HTTP (no suele ser un JSON mal formado respecto al API: si `JSON.parse` fallara en el cliente, verías otro error).

### Checklist en DevTools (F12)

1. **Red (Network)** al enviar el informe:
   - ¿Aparece una fila `POST .../trivy-report` hacia la URL que esperas (p. ej. `http://localhost:8000/...`)?
   - Si aparece en **rojo** o como «(failed)» sin código HTTP: anota el detalle en la columna (p. ej. `net::ERR_CONNECTION_REFUSED`, bloqueo **CORS**).
2. **Consola**:
   - Mensajes tipo *blocked by CORS policy* → el origen del SPA (p. ej. `http://localhost:8080`) debe estar en **`CORS_ORIGINS`** del API y reiniciar `api-gateway`.
   - *Mixed Content* → no mezcles página `https` con API `http://` sin configuración adecuada.

### Comprobar que el archivo no es el problema (misma máquina)

Con el informe de ejemplo del repo (equivalente al informe Trivy “rico” con `Metadata`, `CVSS` anidado, etc.):

```bash
# Windows PowerShell: obtener token y enviar (ajusta scan_id y contraseña)
$r = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" `
  -Body @{ username = "elmero@admon.com"; password = "TU_CLAVE" } -ContentType "application/x-www-form-urlencoded"
$tok = $r.access_token
curl.exe -s -w "`nHTTP:%{http_code}`n" -X POST "http://localhost:8000/api/v1/scans/3/trivy-report" `
  -H "Authorization: Bearer $tok" -H "Content-Type: application/json" `
  --data-binary "@scripts/sample-trivy-full-report.json"
```

Si obtienes **HTTP:202** y `status":"queued"`, el **JSON es aceptado** por el API; el fallo en el navegador es de **URL del API (`VITE_API_BASE_URL`)**, **CORS** o **red**, no del contenido del archivo.

## Referencias

- Flujo API: [scans.py](../services/api-gateway/app/api/v1/scans.py) (`ingest_trivy_report`).
- Procesamiento: [trivy_processing.py](../services/worker/trivy_processing.py).
