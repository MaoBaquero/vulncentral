# FASE 2: Implementar base de datos y modelos.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.


## OBJETIVO:
- Definir modelos SQLAlchemy:
  users, projects, scans, vulnerabilities, audit_logs
- Configurar Alembic
- Crear migraciones iniciales


## REQUISITOS:
- Cumplir ACID
- Definir relaciones correctamente (FK)
- Implementar soft delete (deleted_at)

## SEGURIDAD:
- Hash de contraseñas (NO texto plano)
- Validaciones de campos

## DICCIONARIO DE DATOS (Para creación de migraciones)

### users
- id: BIGINT (PK) Auto Incremental
- name: VARCHAR(255)
- email: VARCHAR(255) UNIQUE
- password: VARCHAR(255)
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### projects
- id: BIGINT (PK) Auto Incremental
- user_id: BIGINT (FK)
- name: VARCHAR(255)
- description: SQLAlchemy Text
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### scans

- id: BIGINT (PK) Auto Incremental
- project_id: BIGINT (FK)
- tool: VARCHAR(255)
- status: VARCHAR(50)
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### vulnerabilities
- id: BIGINT (PK) Auto Incremental
- scan_id: BIGINT (FK)
- title: VARCHAR(255)
- description: SQLAlchemy Text
- severity: VARCHAR(50)
- status: VARCHAR(50)
- cve: VARCHAR(50)
- file_path: VARCHAR(255)
- line_number: integer
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### audit_logs
- id: BIGINT (PK) Auto Incremental
- user_id: BIGINT (FK)
- action: VARCHAR(255)
- entity: VARCHAR(255)
- timestamp: TIMESTAMP

### use_cases
- id: BIGINT (PK) Auto Incremental
- name: VARCHAR(255)
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### roles
- id: BIGINT (PK) Auto Incremental
- name: VARCHAR(255)
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### permissions
- id: BIGINT (PK) Auto Incremental
- name: VARCHAR(255) NULL
- role_id: BIGINT (FK)
- use_case_id: BIGINT (FK)
- C: bolean
- R: bolean
- U: bolean
- D: bolean
- deleted_at: TIMESTAMP NULL
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

---

## ENTREGABLE:
- Modelos
- Configuración Alembic
- Migraciones
