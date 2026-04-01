# Gobierno de migraciones (PostgreSQL compartida)

Una sola instancia PostgreSQL y un solo `Base.metadata` (`vulncentral_db`) implican:

1. **Solo un hilo Alembic** en `services/api-gateway/alembic`. No crear segundas carpetas de migración en el worker.
2. **Revisión de PR**: cualquier cambio que toque tablas usadas por **Core API** e **Ingestion worker** debe mencionarse en el PR y probarse con ambos servicios (o al menos `pytest` en api-gateway + worker).
3. **Orden de despliegue**: si una migración rompe compatibilidad con una versión anterior del worker o del API, desplegar ambas imágenes en la misma ventana o usar migraciones expand/contract en dos fases.
4. **Entorno local**: tras `git pull`, ejecutar `alembic upgrade head` desde `services/api-gateway` con la misma `DATABASE_URL` / `POSTGRES_*` que usará la app.

Ver también [architecture-shared-db-microservices.md](./architecture-shared-db-microservices.md).
