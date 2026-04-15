# Diagramas UML de secuencia (PlantUML) — VulnCentral

Este documento recoge **diagramas de secuencia** en sintaxis [PlantUML](https://plantuml.com/sequence-diagram) alineados con la implementación del repositorio: **Core API (FastAPI)**, **ingestion-worker (Celery)**, **PostgreSQL**, **RabbitMQ**, **volumen compartido de informes** y **frontend (React)**.

**Notas:**

- El login usa **OAuth2 password flow** con cuerpo `application/x-www-form-urlencoded` (`username` = email, `password`). La API responde con **`access_token`** (sin *refresh token*).
- Los JWT se firman con **HS256** y el secreto **`JWT_SECRET`** en el proceso del API (no hay Vault ni HSM en el código).
- Para visualizar: pegar cada bloque `@startuml` … `@enduml` en un renderizador PlantUML o en extensión del IDE.

**Rate limiting:** el endpoint `POST /auth/login` puede estar limitado por **slowapi** según `RATE_LIMIT_LOGIN` en el entorno (no detallado en los diagramas).

---

## 1. Ingesta de informe Trivy (asíncrona)

```plantuml
@startuml
title Ingesta de informe Trivy asíncrona — VulnCentral

actor Cliente as cli
participant "Core API\n(FastAPI)" as API
database "PostgreSQL" as DB
collections "Volumen informes\n(/app/data/reports)" as VOL
queue "RabbitMQ\ncola vulncentral" as MQ
participant "Ingestion worker\n(Celery)" as WK

cli -> API : POST /api/v1/scans/{scanId}/trivy-report\nAuthorization: Bearer JWT\nBody: JSON Trivy
activate API

API -> API : JWTAuthMiddleware:\ndecodifica JWT → user_id
API -> API : require_permission("Gestor escaneos", u)
API -> DB : SELECT User, UseCase, Permission\n(validar permiso actualizar)
DB --> API : OK / error

alt Sin permiso o token inválido
  API --> cli : 401/403
  deactivate API
else Permiso OK
  API -> DB : Validar scan visible\n(get_scan_for_read)
  DB --> API : Scan

  API -> VOL : Escribe JSON\n(scan_{id}_{uuid}.json)
  VOL --> API : Ruta absoluta

  API -> API : enqueue_ingest_trivy_json()\n(send_task vulncentral.ingest_trivy_json)
  API -> MQ : Publica tarea\n(scan_id, file_path, correlation_id)
  MQ --> API : ack

  API -> DB : INSERT audit\n(trivy_report_queued)
  DB --> API : OK

  API --> cli : 202 Accepted\n{status, task_id, file_path, correlation_id}
  deactivate API

  MQ -> WK : Entrega tarea
  activate WK
  WK -> VOL : Lee y valida ruta\n(bajo REPORTS_BASE_DIR)
  VOL --> WK : Contenido JSON
  WK -> DB : Transacción:\nsoft-delete vulns previas +\ninsert nuevas filas +\ncommit
  DB --> WK : OK
  WK -> VOL : Elimina fichero\n(tras commit exitoso)
  WK --> MQ : ACK tarea
  deactivate WK
end

@enduml
```

---

## 2. Autenticación (login JWT)

```plantuml
@startuml
title Flujo de autenticación (login JWT) — VulnCentral

actor Usuario as U
participant "Frontend\n(React)" as FE
participant "API Gateway\n(FastAPI)" as GW
database "PostgreSQL" as DB

U -> FE : Ingresa email y contraseña
FE -> GW : POST /auth/login\nContent-Type: application/x-www-form-urlencoded\nusername={email}&password={***}
activate GW

GW -> DB : SELECT User WHERE email\nAND deleted_at IS NULL
DB --> GW : Usuario o vacío

alt Usuario inexistente o password inválida
  GW -> DB : INSERT audit (login_failed)
  DB --> GW : OK
  GW --> FE : 401\n{error: invalid_credentials}
  FE --> U : Mensaje de error
else Usuario sin rol
  GW -> DB : INSERT audit (login_failed_no_role)
  DB --> GW : OK
  GW --> FE : 401\n{error: invalid_credentials}
  FE --> U : Mensaje de error
else Credenciales y rol válidos
  GW -> GW : verify_password(password, hash bcrypt)
  GW -> GW : create_access_token()\nFirma JWT HS256 con JWT_SECRET\nclaims: sub, exp, iat, role_id
  GW -> DB : INSERT audit (login_success)
  DB --> GW : OK
  GW --> FE : 200\n{access_token, token_type: bearer, expires_in}
  FE -> FE : Guarda token\n(sessionStorage / estado)
  FE --> U : Acceso concedido
end
deactivate GW

@enduml
```

---

## 3. Petición autenticada a la API (GET /api/v1/… con JWT)

```plantuml
@startuml
title Petición autenticada GET /api/v1/scans — VulnCentral

actor Cliente as C
participant "API Gateway\n(FastAPI)" as GW
participant "JWTAuthMiddleware" as JWT
database "PostgreSQL" as DB

C -> GW : GET /api/v1/scans\nAuthorization: Bearer {token}
activate GW
GW -> JWT : dispatch(request)
activate JWT

alt Sin cabecera Bearer o token vacío
  JWT --> C : 401 missing_token / invalid_token
  deactivate JWT
  deactivate GW
else Token presente
  JWT -> JWT : decode_access_token(token)\n(HS256, JWT_SECRET)
  alt Token expirado
    JWT --> C : 401 token_expired
    deactivate JWT
    deactivate GW
  else Token inválido o mal configurado
    JWT --> C : 401 invalid_token / 500 configuration_error
    deactivate JWT
    deactivate GW
  else Token válido
    JWT -> JWT : request.state.user_id = sub
    JWT -> GW : call_next hacia ruta /api/v1/scans
    deactivate JWT

    GW -> DB : SELECT User (+ Role)\nWHERE id = user_id
    DB --> GW : User

    alt Usuario borrado o no encontrado
      GW --> C : 401 invalid_user
      deactivate GW
    else Usuario OK
      GW -> DB : SELECT UseCase "Gestor escaneos"\n+ Permission (perm_r)
      DB --> GW : Permiso sí/no

      alt Sin permiso lectura escaneos
        GW --> C : 403 forbidden
        deactivate GW
      else Permiso OK
        GW -> DB : SELECT Scan (+ Project)\nfiltrado por visibilidad
        DB --> GW : Lista de escaneos
        GW --> C : 200 [ScanRead, ...]
        deactivate GW
      end
    end
  end
end

@enduml
```

---

## 4. Flujo en el navegador: login + acción (escaneo + informe Trivy)

```plantuml
@startuml
title Flujo navegador: login y carga de informe Trivy — VulnCentral

actor Usuario as U
participant "Frontend\n(React)" as FE
participant "API Gateway\n(FastAPI)" as GW
participant "JWTAuthMiddleware" as JWT
database "PostgreSQL" as DB

U -> FE : Abre /login e ingresa credenciales
FE -> GW : POST /auth/login\n(form: username, password)
activate GW
GW -> DB : Validar usuario y rol
DB --> GW : User
GW -> GW : Firma JWT
GW --> FE : 200 {access_token, expires_in}
deactivate GW

FE -> FE : setToken → sessionStorage\n(TOKEN_KEY)

FE -> GW : GET /auth/me\nAuthorization: Bearer
activate GW
GW -> JWT : dispatch
activate JWT
JWT -> JWT : decode_access_token\n→ request.state.user_id
JWT -> GW : call_next
deactivate JWT
GW -> DB : get_current_user +\npermissions_matrix_for_role
DB --> GW : Perfil + permisos
GW --> FE : 200 {id, name, email, permissions, ...}
deactivate GW

U -> FE : Flujo guiado:\ncrear escaneo y pegar JSON Trivy

FE -> GW : POST /api/v1/scans\nBearer + JSON {project_id, tool, status}
activate GW
GW -> DB : RBAC + crear Scan + audit
DB --> GW : scan id
GW --> FE : 201 {id, ...}
deactivate GW

FE -> GW : POST /api/v1/scans/{id}/trivy-report\nBearer + JSON Trivy
activate GW
GW -> DB : RBAC + validar scan + audit cola
GW --> FE : 202 {task_id, correlation_id, ...}
deactivate GW

FE --> U : Mensaje "encolado" / siguiente paso UI

@enduml
```

---

## 5. Alta de usuario y creación proyecto + escaneo (CRUD con RBAC)

```plantuml
@startuml
title CRUD con RBAC: usuarios y proyecto+escaneo — VulnCentral

actor Operador as OP
participant "API Gateway\n(FastAPI)" as GW
database "PostgreSQL" as DB

alt A — Alta de usuario (POST /api/v1/users)
  OP -> GW : POST /api/v1/users\nBearer + JSON UserCreate
  activate GW
  GW -> GW : JWT + get_current_user
  GW -> DB : RBAC: UseCase "Gestor usuarios"\nPermission perm_c
  DB --> GW : Permitido / denegado
  alt Sin permiso crear usuarios
    GW --> OP : 403 forbidden
  else Permiso OK
    GW -> DB : SELECT User por email\n(unicidad)
    alt Email duplicado
      GW --> OP : 409 conflict
    else Email libre
      GW -> DB : SELECT Role por role_id
      DB --> GW : Rol válido
      GW -> GW : User.set_password(bcrypt)
      GW -> DB : INSERT User + commit
      GW -> DB : INSERT audit (user_create)
      GW --> OP : 201 UserRead
    end
  end
  deactivate GW

else B — Proyecto y escaneo (POST proyecto luego POST escaneo)
  OP -> GW : POST /api/v1/projects\nBearer + JSON ProjectCreate
  activate GW
  GW -> DB : RBAC: "Gestor proyectos" perm_c\n+ reglas user_id (global vs propio)
  GW -> DB : Validar usuario existente\nINSERT Project + audit
  DB --> GW : project_id
  GW --> OP : 201 ProjectRead
  deactivate GW

  OP -> GW : POST /api/v1/scans\nBearer + JSON {project_id, tool, status}
  activate GW
  GW -> DB : RBAC: "Gestor escaneos" perm_c
  GW -> DB : get_project_for_read\n(visibilidad del proyecto)
  alt Proyecto no visible
    GW --> OP : 403/404 según política
  else Proyecto OK
    GW -> DB : INSERT Scan + audit (scan_create)
    GW --> OP : 201 ScanRead
  end
  deactivate GW
end

@enduml
```

---

## Referencias de código

- Login y JWT: [`services/api-gateway/app/api/auth.py`](../services/api-gateway/app/api/auth.py), [`services/api-gateway/app/security/jwt_tokens.py`](../services/api-gateway/app/security/jwt_tokens.py)
- Middleware JWT: [`services/api-gateway/app/middleware/jwt_auth.py`](../services/api-gateway/app/middleware/jwt_auth.py)
- RBAC: [`services/api-gateway/app/rbac.py`](../services/api-gateway/app/rbac.py)
- Ingesta Trivy y escaneos: [`services/api-gateway/app/api/v1/scans.py`](../services/api-gateway/app/api/v1/scans.py)
- Worker: [`services/worker/tasks/tasks.py`](../services/worker/tasks/tasks.py), [`services/worker/trivy_processing.py`](../services/worker/trivy_processing.py)
- Frontend auth y flujo: [`services/frontend/src/context/AuthContext.jsx`](../services/frontend/src/context/AuthContext.jsx), [`services/frontend/src/pages/FlowNewPage.jsx`](../services/frontend/src/pages/FlowNewPage.jsx)
