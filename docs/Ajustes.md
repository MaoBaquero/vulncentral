# Ajustes operativos documentados

Registro de cambios de comportamiento acordados fuera del flujo habitual de fases. Cada entrada debe mantener las secciones siguientes cuando aplique.

---

## Ajuste: rol Inspector (lectura transversal, sin crear proyectos ni escaneos)

### Objetivo del ajuste

Alinear el rol **Inspector** con la política operativa:

- **No** puede crear proyectos nuevos.
- **No** puede crear escaneos nuevos.
- **Sí** puede ver **todos** los proyectos (y, vía la misma regla de lectura IDOR, escaneos y vulnerabilidades enlazados), independientemente del propietario del proyecto.
- **Sí** puede crear y editar vulnerabilidades (según permisos RBAC del caso de uso «Gestor vulnerabilidades»).

### Archivos modificados

| Archivo | Descripción breve |
|---------|-------------------|
| [`services/api-gateway/app/idor.py`](../services/api-gateway/app/idor.py) | Nueva función `has_cross_project_read` (Administrator/Master vía alcance global, más Inspector). Usada en `visible_project_ids`, `get_project_for_read`, `get_scan_for_read` y `get_vulnerability_for_read` para lecturas/listados. `has_global_data_access` se mantiene para mutaciones sensibles en proyectos (p. ej. creación/reasignación). |
| [`services/api-gateway/app/scripts/seed.py`](../services/api-gateway/app/scripts/seed.py) | Matriz de permisos: Inspector + «Gestor escaneos» pasa `perm_c` a **false** (sigue con lectura/actualización/borrado según el resto de flags). |
| [`services/api-gateway/tests/test_f8_security.py`](../services/api-gateway/tests/test_f8_security.py) | Pruebas Fase 8: Inspector puede GET proyecto ajeno; 403 en POST proyecto y POST escaneo; fixture `inspector_headers`. |
| [`README.md`](../README.md) | Apartado endurecimiento Fase 8: texto IDOR actualizado (Inspector y lectura transversal). |

### Archivos creados

| Archivo | Descripción breve |
|---------|-------------------|
| [`docs/Ajustes.md`](./Ajustes.md) | Este documento (registro del ajuste y plantilla para futuros ajustes). |

### Comandos utilizados

Desde `services/api-gateway`:

```bash
python -m pytest tests/test_f8_security.py -q
```

Tras desplegar o en una base ya sembrada, para **actualizar** la fila de permisos del Inspector en «Gestor escaneos» (y el resto de filas que el seed sincroniza):

```bash
python -m app.scripts.seed
```

(o el procedimiento equivalente que use tu entorno: `docker compose exec api-gateway python -m app.scripts.seed`, etc.)

### Problemas comunes y soluciones

| Problema | Solución |
|----------|----------|
| Inspector sigue pudiendo crear escaneos en la UI o recibe 403 inesperado en lectura | Comprueba que el seed se haya ejecutado de nuevo: la tabla `permissions` debe tener `perm_c = 0` para el rol Inspector y el caso de uso «Gestor escaneos». Reinicia sesión para refrescar JWT y payload de `/auth/me`. |
| Listados vacíos o 404 en proyectos ajenos para Inspector | Verifica que el código desplegado incluya `has_cross_project_read` en `idor.py` y que el usuario tenga rol Inspector cargado (`joinedload` en `get_current_user`). |
| Tests Fase 8 fallan tras cambios locales | Ejecuta `pytest tests/test_f8_security.py -q` y revisa que no haya datos residuales en otra suite que reutilice la misma BD. |

### Complejidad, impacto y riesgo

- **Complejidad**: baja-media (cambios acotados en IDOR, seed y tests).
- **Impacto**: medio — cambia el modelo de confidencialidad del rol Inspector en **lectura** (pasa a ver datos de todos los proyectos).
- **Riesgo**: bajo si las pruebas de Fase 8 y la revisión de endpoints que combinan RBAC + IDOR son correctas; conviene no duplicar lógica de filtrado por `user_id` fuera de `idor` sin revisión.

---

## Corrección: ingesta Trivy en Docker (worker / `PYTHONPATH`)

### Objetivo

Que la tarea Celery `vulncentral.ingest_trivy_json` pueda importar `trivy_processing` en procesos **prefork** del worker; sin ello el API devolvía 202 «encolado» pero la base no reflejaba vulnerabilidades.

### Archivos modificados / creados

| Archivo | Descripción |
|---------|-------------|
| [`services/worker/Dockerfile`](../services/worker/Dockerfile) | `ENV PYTHONPATH=/app` en la imagen final. |
| [`docs/diagnostico-ingesta-trivy-carga.md`](./diagnostico-ingesta-trivy-carga.md) | Guía de verificación (`docker compose ps`, logs, curl, causas frecuentes). |
| [`scripts/smoke-trivy-minimal.json`](../scripts/smoke-trivy-minimal.json) | JSON mínimo con una vulnerabilidad para pruebas manuales. |

### Comandos

```bash
docker compose build worker && docker compose up -d worker
docker compose logs worker --tail=50
```

---

---

## Documentación: «Failed to fetch» al cargar informe Trivy (SPA)

### Objetivo

Dejar constancia de que el mensaje **Failed to fetch** suele deberse a **CORS / URL del API / red**, no a un JSON Trivy inválido; guía en [diagnostico-ingesta-trivy-carga.md](./diagnostico-ingesta-trivy-carga.md) (sección 5).

### Archivos tocados

| Archivo | Cambio |
|---------|--------|
| [docs/diagnostico-ingesta-trivy-carga.md](./diagnostico-ingesta-trivy-carga.md) | Checklist DevTools + prueba `curl` con `scripts/sample-trivy-full-report.json`. |
| [scripts/sample-trivy-full-report.json](../scripts/sample-trivy-full-report.json) | Muestra de informe Trivy “rico” para pruebas. |
| [.env.example](../.env.example) | Comentarios explícitos en `CORS_ORIGINS` y `VITE_API_BASE_URL`. |
| [services/frontend/src/services/apiClient.js](../services/frontend/src/services/apiClient.js) | Mensaje ampliado en errores de red (`fetch`). |

---

## Ajuste: botón «Subir» informe Trivy desde fichero JSON (Vulnerabilidades)

### Objetivo del ajuste

Ofrecer en la vista **Vulnerabilidades**, junto al flujo existente de **Cargar** (pegado de JSON en modal) y **Crear**, un tercer botón **Subir** que abra el selector de archivos del sistema para elegir un `.json` de Trivy y enviarlo al mismo endpoint `POST /api/v1/scans/{scan_id}/trivy-report` (cola Celery + worker), sin cambiar contrato de API.

### Archivos modificados

| Archivo | Descripción breve |
|---------|-------------------|
| [`services/frontend/src/pages/VulnerabilitiesPage.jsx`](../services/frontend/src/pages/VulnerabilitiesPage.jsx) | Botón **Subir** (misma visibilidad RBAC y contexto de escaneo que **Cargar**), `<input type="file">` oculto, lectura con `FileReader` y `uploadTrivyReport` desde [`services/frontend/src/services/scans.js`](../services/frontend/src/services/scans.js); feedback de carga y mensaje breve «Encolado» tras éxito. |
| [`docs/Ajustes.md`](./Ajustes.md) | Esta entrada. |

### Archivos creados

Ninguno.

### Comandos utilizados

Verificación manual en navegador (contexto de escaneo activo desde Escaneos) y, opcionalmente, compilación del frontend:

```bash
cd services/frontend && npm run build
```

### Problemas comunes y soluciones

| Problema | Solución |
|----------|----------|
| Error al enviar o JSON inválido | Mismo criterio que **Cargar** con pegado: el cliente parsea el texto con `JSON.parse` antes del `POST`; corregir el fichero o exportar de nuevo desde Trivy. |
| API responde 202 pero la tabla no muestra vulnerabilidades | Revisar worker, RabbitMQ y volumen compartido de informes; ver [diagnostico-ingesta-trivy-carga.md](./diagnostico-ingesta-trivy-carga.md). |
| Navegador lento o fallo al leer un JSON enorme | Informes muy grandes consumen memoria en el cliente; valorar trocear o subir vía **Cargar** por partes solo si el modelo de negocio lo permite (el endpoint actual espera un único JSON completo). |

### Complejidad, impacto y riesgo

- **Complejidad**: baja (solo React y servicio existente).
- **Impacto**: bajo–medio — mejora operativa; mismos datos y mismo endpoint que **Cargar**.
- **Riesgo**: bajo; riesgos residuales: JSON mal formado y ficheros extremadamente grandes en memoria del navegador.

---

*Referencias de requisitos: `.cursor/prompts/Ajuste_Operativo_1.md`, `.cursor/prompts/Ajuste_Operativo_2.md`.*
