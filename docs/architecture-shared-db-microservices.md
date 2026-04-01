# Arquitectura: servicios desplegables con PostgreSQL compartida

Este documento implementa la **Fase 0** del plan de evolución (límites lógicos) y resume el **gobierno de esquema (Fase 3)** sobre una **única instancia PostgreSQL** compartida por los servicios de aplicación.

## Servicios desplegables

| Servicio (rol) | Artefacto | Responsabilidad principal |
|----------------|-------------|---------------------------|
| **Frontend** | `services/frontend` (React + Nginx) | UI; solo habla con la API pública por HTTP. |
| **Core API** | `services/api-gateway` (FastAPI) | JWT, RBAC, CRUD expuesto en `/api/v1`, encolado de ingesta Trivy, escritura/lectura según la matriz siguiente. |
| **Ingestion worker** | `services/worker` (Celery) | Consume tareas AMQP, lee JSON Trivy del volumen compartido, normaliza y persiste vulnerabilidades. |

Infraestructura compartida: **PostgreSQL**, **RabbitMQ**, volumen **`reports_data`**.

## Matriz tabla → servicio dueño (lectura / escritura)

Convención: **W** = creación/actualización/borrado lógico habitual; **R** = lecturas en flujos normales. Ambos servicios usan la **misma BD**; el dueño indica quién debe iniciar cambios de esquema y reglas de negocio para escritura.

| Tabla | Core API | Ingestion worker | Notas |
|-------|----------|------------------|--------|
| `users` | W / R | — | Seed y CRUD según RBAC. |
| `roles` | R (seed) | — | |
| `use_cases` | R (seed) | — | |
| `permissions` | R (seed) | — | |
| `projects` | W / R | — | |
| `scans` | W / R | R | Worker comprueba existencia del scan; no crea scans. |
| `vulnerabilities` | W / R | W / R | API: CRUD manual vía `/api/v1/vulnerabilities`. Worker: soft-delete de activas del scan + insert masivo tras informe Trivy. |
| `audit_logs` | W / R | — | |

Si en el futuro se restringe el worker a solo lectura de `scans`, la matriz se actualiza aquí.

## Modelo de datos compartido (Fase 2A)

Los modelos SQLAlchemy y `Base.metadata` viven en el paquete **`vulncentral_db`** ([`packages/vulncentral-db`](../packages/vulncentral-db)). Las migraciones Alembic siguen en `services/api-gateway/alembic` y deben importar ese metadata.

## Gobierno de esquema (Fase 3)

1. **Un solo hilo de migraciones**: ejecutar `alembic upgrade head` desde el contexto del API Gateway (misma URL que producción).
2. **Cambios que afecten tablas usadas por API y worker** (p. ej. `vulnerabilities`, `scans`): revisión conjunta; desplegar **API y worker** en la misma ventana cuando el cambio sea incompatible con versiones anteriores.
3. **No** introducir segunda base PostgreSQL para “microservicios” sin un proyecto de migración de datos explícito.

## Referencias

- Contrato de cola: [amqp-ingest-contract.md](./amqp-ingest-contract.md)
- Código ingesta: `services/worker/trivy_processing.py`, tarea `vulncentral.ingest_trivy_json`.
