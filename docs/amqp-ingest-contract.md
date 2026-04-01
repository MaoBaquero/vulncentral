# Contrato AMQP: ingesta de informes Trivy

**Cola:** `vulncentral` (configuración Celery `task_default_queue`).  
**Nombre de tarea:** `vulncentral.ingest_trivy_json`  
**Versión del contrato:** `1` (campo opcional en payload para evolución futura).

## Payload (argumentos posicionales de la tarea)

| Orden | Campo | Tipo | Obligatorio | Descripción |
|-------|--------|------|-------------|-------------|
| 1 | `scan_id` | `int` | Sí | ID del escaneo en `scans.id` (debe existir y no estar soft-deleted). |
| 2 | `file_path` | `str` | Sí | Ruta **absoluta** del JSON en el volumen compartido (validada bajo `REPORTS_BASE_DIR`). |
| 3 | `correlation_id` | `str` \| `null` | No | UUID u otro id para trazas entre API, cola y worker (logs). |

Serialización Celery: JSON (`task_serializer=json`).

## Idempotencia y reintentos

- Reintentos automáticos del worker ante errores **transitorios** (p. ej. DB); no reintenta errores de validación (`ValueError`, `ValidationError`, `JSONDecodeError`).
- Reprocesar el mismo `scan_id` con un **nuevo** fichero sustituye vulnerabilidades activas del scan (soft-delete + insert) según la lógica actual de negocio.
- Tras **commit** exitoso en PostgreSQL, el worker **elimina** el fichero JSON; fallos previos al commit **no** borran el archivo.

## Productor (Core API)

- Tras validar el cuerpo Trivy y escribir el archivo, el API publica la tarea con `scan_id`, ruta absoluta y `correlation_id` (p. ej. UUID v4).

## Errores

- Mensaje inválido o ruta fuera de `REPORTS_BASE_DIR`: tarea fallida sin reintento infinito; el JSON permanece en disco si no hubo commit.
