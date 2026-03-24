# FASE 4: Implementar API Gateway.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- CRUD:
  - users
  - projects
  - scans
  - vulnerabilities

## REQUISITOS:
- Validación con Pydantic
- Manejo de errores HTTP estándar
- Versionado API (/api/v1/)
- Validar JSON de entrada (estructura tipo Trivy)

## SEGURIDAD:
- Validar tamaño de archivos
- Sanitización de inputs

##  Enums

Crea un Enum en Python para las severidades y las vulnerabilidades heredando de str y Enum para que sean serializables directamente a JSON en las respuestas del API.

### Severity
- LOW
- MEDIUM
- HIGH
- CRITICAL

### Vulnerability 
- OPEN
- IN_PROGRESS
- MITIGATED
- ACCEPTED

---


## ENTREGABLE:
- Endpoints completos
- Validaciones
- Enums