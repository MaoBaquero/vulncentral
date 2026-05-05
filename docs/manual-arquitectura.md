# Manual de Arquitectura — VulnCentral

**Versión:** 1.0
**Proyecto:** VulnCentral — Plataforma DevSecOps
**Institución:** Fundación Universitaria UNIMINUTO
**Programa:** Especialización en Ciberseguridad · Seguridad Entornos Cloud DevOps
**Autores:** Ing. Argel Ochoa Ronald David · Ing. Baquero Soto Mauricio · Ing. Buitrago Guiot Óscar Javier · Ing. Estefanía Naranjo Novoa

---

## 1. Descripción de la Arquitectura de Microservicios

VulnCentral implementa una **arquitectura de microservicios asíncronos orquestada por eventos (Event-Driven)**. El sistema divide las responsabilidades en contenedores independientes que se comunican a través de una red aislada (`vulncentral_net`) y un broker de mensajes (RabbitMQ).

Una particularidad fundamental es el **"Patrón de Base de Datos Compartida por Paquete"**: aunque son microservicios independientes, tanto el API como el Worker se conectan a la misma instancia PostgreSQL. Para evitar duplicar código ORM, se extrajo un paquete Python compartido (`packages/vulncentral-db`) que se inyecta durante el build de Docker. Esto garantiza integridad referencial sin acoplar los ciclos de vida de los contenedores.

### Flujo de procesamiento central

1. El usuario sube un informe Trivy (JSON) desde el frontend.
2. El API Gateway valida, persiste el archivo en el volumen `reports_data` y publica en RabbitMQ únicamente el `scan_id` y la `ruta_absoluta` — nunca el payload completo.
3. El API responde inmediatamente con **HTTP 202 Accepted**, sin bloquear al cliente.
4. El Worker Celery consume el mensaje, lee el archivo del volumen, normaliza las vulnerabilidades y las persiste en PostgreSQL mediante una transacción ACID.
5. Tras el commit exitoso, el Worker elimina el fichero JSON del volumen.

### Servicios desplegables

| Servicio | Artefacto | Responsabilidad principal |
|----------|-----------|--------------------------|
| **Frontend** | `services/frontend` (React + Nginx) | SPA; solo habla con la API pública por HTTP. RBAC oculta elementos según rol. |
| **Core API** | `services/api-gateway` (FastAPI) | JWT, RBAC, CRUD en `/api/v1`, encolado de ingesta Trivy, escritura/lectura BD. |
| **Ingestion Worker** | `services/worker` (Celery) | Consume tareas AMQP, lee JSON Trivy del volumen compartido, normaliza y persiste vulnerabilidades. |

Infraestructura compartida: **PostgreSQL 16**, **RabbitMQ 3.13**, volumen **`reports_data`**.

---

## 2. Decisiones de Diseño y Patrones Utilizados

| Patrón / Decisión | Implementación en VulnCentral | Justificación |
| :--- | :--- | :--- |
| **API Gateway Pattern** | Servicio `api-gateway` como punto único de entrada | Centraliza autenticación, rate limiting y enrutamiento |
| **Choreography Saga** | API publica en RabbitMQ; Worker procesa de forma independiente | Desacopla el tiempo de respuesta HTTP del procesamiento pesado. Responde HTTP 202 inmediato |
| **Proxy de Referencia** | El API publica solo `scan_id` y `ruta_absoluta` por la cola AMQP | Evita saturar la red y la memoria del broker con payloads masivos (>10 MB) |
| **Shared-Nothing (Lógica)** | Worker y API no comparten estado en memoria; solo conexión a PostgreSQL | Simplifica transacciones ACID sin requerir eventos de sincronización complejos |
| **Repository Pattern** | Capa de datos centralizada en `vulncentral-db` (SQLAlchemy 2.x) | Desacopla la lógica de negocio del motor de BD; facilita testing y migración futura |
| **Dependency Injection** | `FastAPI Depends()` para sesiones, usuarios autenticados y permisos | Permite probar componentes de forma aislada sin acoplamiento directo |
| **Defense in Depth (OWASP)** | Validación MIME, Rate Limiting, prevención Path Traversal, IDOR a nivel SQL | Múltiples capas de seguridad redundantes; ninguna capa es el único control |
| **Soft Delete** | Los registros no se eliminan físicamente de la base de datos | Preserva trazabilidad de auditoría y permite recuperación ante errores operativos |

---

## 3. Justificación de Cada Componente

### 3.1 Frontend — React 18 + Vite + Nginx

Nginx sirve los archivos estáticos compilados y actúa como proxy inverso hacia el API Gateway, evitando exponer el servidor Vite en producción. El RBAC del lado del cliente oculta elementos de la interfaz según el rol del usuario autenticado, complementando (sin reemplazar) los controles del backend.

### 3.2 API Gateway — FastAPI + Pydantic (Python 3.12)

FastAPI fue seleccionado por su modelo de I/O asíncrono basado en ASGI, que permite manejar múltiples conexiones concurrentes sin bloquear el event loop. Pydantic valida el esquema del informe Trivy en tiempo de ejecución al milisegundo, rechazando payloads malformados antes de que lleguen a la lógica de negocio.

### 3.3 Worker — Celery + RabbitMQ 3.13

Celery aísla el procesamiento CPU/IO intensivo (parseo de JSON, normalización, inserción masiva) del ciclo de vida del API. Si el parseo falla, el API no se ve afectado; Celery gestiona reintentos automáticos ante errores **transitorios** (DB, red), pero no reintenta errores de validación (`ValueError`, `ValidationError`, `JSONDecodeError`). RabbitMQ garantiza entrega confiable con persistencia en disco y soporte de dead-letter queues.

### 3.4 Volumen Compartido — `reports_data`

Actúa como almacenamiento temporal entre el API y el Worker, evitando transferir el payload JSON completo por la cola AMQP. El Worker valida que la ruta esté bajo `REPORTS_BASE_DIR` para prevenir Path Traversal. Justificado para on-premise sin requerir S3/MinIO en esta fase.

### 3.5 Persistencia — PostgreSQL 16 + SQLAlchemy 2.x + Alembic

PostgreSQL fue seleccionado sobre soluciones NoSQL porque el modelo de datos requiere JOINs complejos para calcular permisos RBAC y aplicar condiciones IDOR a nivel de consulta (`WHERE project_id IN (SELECT ... WHERE user_id = current_user)`). Alembic gestiona un único hilo de migraciones versionadas y reversibles desde `services/api-gateway/alembic`.

### 3.6 Autenticación — JWT (HS256) + passlib + slowapi

JWT permite autenticación stateless habilitando escalabilidad horizontal sin sesiones en servidor. `passlib` con bcrypt gestiona el hashing seguro de contraseñas. `slowapi` implementa rate limiting configurable vía `RATE_LIMIT_LOGIN` (por defecto `5/minute`) para mitigar fuerza bruta y credential stuffing.

### 3.7 Matriz de propiedad de tablas

| Tabla | Core API | Ingestion Worker | Notas |
|-------|----------|-----------------|-------|
| `users` | W / R | — | Seed y CRUD según RBAC |
| `roles` | R (seed) | — | Solo lectura en tiempo de ejecución |
| `use_cases` | R (seed) | — | |
| `permissions` | R (seed) | — | |
| `projects` | W / R | — | |
| `scans` | W / R | R | Worker comprueba existencia; no crea scans |
| `vulnerabilities` | W / R | W / R | Worker: soft-delete previas + insert masivo |
| `audit_logs` | W / R | — | Registro inmutable de acciones |

---

## 4. Diagramas UML

> Todos los diagramas están definidos como código en sintaxis **Mermaid** y **PlantUML**, directamente versionables en el repositorio. Se pueden renderizar en GitHub, GitLab, VS Code (extensión Mermaid), Obsidian o cualquier visor compatible.

---

### 4.1 Diagrama de Componentes

> Visión general de la arquitectura: capas, paquete ORM compartido y separación de responsabilidades entre el API Gateway y el Worker.

```mermaid
graph TB
    subgraph Cliente["capa de presentación"]
        UI["React SPA\n+ Nginx :80/:443"]
    end

    subgraph API["api gateway  —  services/api-gateway"]
        AG["FastAPI · Python 3.12\nPydantic · ASGI"]
        AUTH["Auth / RBAC\nJWT HS256 · slowapi"]
        AG --> AUTH
    end

    subgraph Async["procesamiento asíncrono"]
        Q["RabbitMQ 3.13\ncola: vulncentral\ntarea: ingest_trivy_json"]
        W["Celery Worker\nparseo · normalización\nreintentos exponenciales"]
        VOL["Volumen\nreports_data\n/app/data/reports"]
        Q --> W
        W -->|"lee / elimina JSON"| VOL
    end

    subgraph Persist["persistencia"]
        ORM["vulncentral-db\nSQLAlchemy 2.x · Alembic\npaquete compartido"]
        PG[("PostgreSQL 16\nACID · JOINs RBAC")]
        ORM --> PG
    end

    subgraph CICD["ci/cd  —  shift-left"]
        GH["GitHub Actions"]
        SEC["Bandit · Semgrep · Gitleaks\nTrivy · ZAP · pip-audit"]
        GH --> SEC
    end

    UI -->|"HTTPS"| AG
    AG -->|"HTTP 202\npublica scan_id + ruta"| Q
    AG -->|"guarda JSON"| VOL
    AG --> ORM
    W --> ORM
```

---

### 4.2 Diagrama de Despliegue

> Contenedores Docker, red aislada `vulncentral_net`, volúmenes y límites de memoria por servicio.

```mermaid
graph TB
    Browser["navegador\nHTTPS :443"]

    subgraph Net["red: vulncentral_net (bridge)"]

        subgraph N1["Nodo 1 — Entrada"]
            Nginx["Nginx\n:80 / :443\nreverse proxy"]
            FE["Frontend React\nestáticos compilados"]
            API["API Gateway\nFastAPI :8000\nmáx 384 MB"]
            Nginx --> FE
            Nginx --> API
        end

        subgraph N2["Nodo 2 — Procesamiento"]
            W1["Worker réplica 1\nCelery · máx 384 MB"]
            W2["Worker réplica 2\nCelery · máx 384 MB"]
            WN["Worker réplica N\nescala horizontal"]
        end

        subgraph N3["Nodo 3 — Datos"]
            PG[("PostgreSQL 16\n:5432 · máx 512 MB")]
            RMQ["RabbitMQ 3.13\nAMQP :5672\nmgmt :15672 · máx 512 MB"]
            VOL[/"Volumen reports_data\nalmacenamiento temporal JSON"/]
        end

        API -->|"AMQP: scan_id + ruta"| RMQ
        API -->|"escribe JSON"| VOL
        API -->|"SQL"| PG
        RMQ --> W1 & W2 & WN
        W1 & W2 -->|"lee · elimina JSON"| VOL
        W1 & W2 -->|"INSERT vulns"| PG
    end

    Browser -->|"HTTPS"| Nginx
```

> **Escalado horizontal de workers:**
> ```bash
> # Docker Compose
> docker compose up --scale worker=4 -d
>
> # Docker Swarm (producción)
> docker service scale vulncentral_worker=5
> ```

---

### 4.3 Diagrama de Secuencia — Flujo Crítico: Autenticación JWT

> Flujo completo con OAuth2 password flow, verificación bcrypt, rate limiting, generación JWT y registro de auditoría. Incluye los tres caminos de error.

```mermaid
sequenceDiagram
    actor Usuario
    participant FE as Frontend (React)
    participant GW as API Gateway (FastAPI)
    participant RL as Rate Limiter (slowapi)
    participant DB as PostgreSQL

    Usuario->>FE: ingresa email + contraseña
    FE->>GW: POST /auth/login\ncontent-type: x-www-form-urlencoded\nusername={email}&password={***}

    GW->>RL: verificar límite RATE_LIMIT_LOGIN (5/min por IP)
    alt límite excedido
        RL-->>FE: HTTP 429 Too Many Requests
        FE-->>Usuario: error — demasiados intentos
    end

    GW->>DB: SELECT User WHERE email=? AND deleted_at IS NULL
    alt usuario no encontrado
        DB-->>GW: vacío
        GW->>DB: INSERT audit (login_failed)
        GW-->>FE: HTTP 401 invalid_credentials
        FE-->>Usuario: credenciales incorrectas
    end

    DB-->>GW: datos usuario + hash bcrypt + role_id
    alt usuario sin rol asignado
        GW->>DB: INSERT audit (login_failed_no_role)
        GW-->>FE: HTTP 401 invalid_credentials
        FE-->>Usuario: credenciales incorrectas
    end

    GW->>GW: verify_password(password, hash) — bcrypt
    GW->>GW: create_access_token()\nfirma JWT HS256 con JWT_SECRET\nclaims: sub, exp, iat, role_id
    GW->>DB: INSERT audit (login_success, ip, timestamp)
    GW-->>FE: HTTP 200 { access_token, token_type: bearer, expires_in }
    FE->>FE: setToken → sessionStorage (TOKEN_KEY)
    FE-->>Usuario: acceso concedido — redirige a dashboard según rol
```

---

### 4.4 Diagrama de Secuencia — Flujo Crítico: Ingesta de Informe Trivy

> Flujo asíncrono completo: validación RBAC, escritura en volumen, publicación AMQP, HTTP 202 inmediato y procesamiento en background por el Worker.

```mermaid
sequenceDiagram
    actor Cliente
    participant FE as Frontend (React)
    participant GW as API Gateway (FastAPI)
    participant DB as PostgreSQL
    participant VOL as Volumen reports_data
    participant MQ as RabbitMQ (cola vulncentral)
    participant WK as Ingestion Worker (Celery)

    Cliente->>FE: selecciona escaneo y pega JSON Trivy
    FE->>GW: POST /api/v1/scans/{scanId}/trivy-report\nAuthorization: Bearer JWT\nBody: JSON Trivy

    GW->>GW: JWTAuthMiddleware — decodifica JWT → user_id
    GW->>GW: require_permission("Gestor escaneos")
    GW->>DB: SELECT User + UseCase + Permission (validar RBAC)
    alt sin permiso o token inválido
        DB-->>GW: denegado
        GW-->>FE: HTTP 401 / 403
    end

    GW->>DB: get_scan_for_read — validar scan visible
    DB-->>GW: Scan OK
    GW->>VOL: escribe scan_{id}_{uuid}.json
    VOL-->>GW: ruta absoluta

    GW->>MQ: send_task vulncentral.ingest_trivy_json\n(scan_id, file_path, correlation_id)
    MQ-->>GW: ACK
    GW->>DB: INSERT audit (trivy_report_queued)
    GW-->>FE: HTTP 202 Accepted\n{ task_id, correlation_id, file_path }
    FE-->>Cliente: mensaje "procesando en background"

    Note over MQ,WK: procesamiento asíncrono — independiente del API

    MQ->>WK: entrega tarea
    WK->>VOL: lee y valida ruta (bajo REPORTS_BASE_DIR)
    VOL-->>WK: contenido JSON Trivy
    WK->>DB: BEGIN TRANSACTION\nsoft-delete vulns previas del scan\nINSERT nuevas vulnerabilidades\nCOMMIT
    DB-->>WK: OK
    WK->>VOL: elimina fichero JSON (post-commit)
    WK-->>MQ: ACK tarea completada
```

---

### 4.5 Diagrama de Casos de Uso — Actores e Interacciones RBAC

> Los cuatro actores del sistema RBAC. El frontend oculta opciones no permitidas; el backend valida en cada endpoint de forma independiente.

```mermaid
graph TB
    subgraph Actores
        U((usuario\nautenticado))
        ADM((administrador))
        MAE((maestro))
        INS((inspector))
    end

    subgraph Auth["autenticación"]
        Login["iniciar sesión\nPOST /auth/login"]
        Logout["cerrar sesión"]
        Pwd["cambiar contraseña"]
    end

    subgraph GestionUsuarios["gestión de usuarios"]
        CU["crear / editar / desactivar usuarios\nPOST·PUT /api/v1/users"]
        RO["asignar roles"]
        AU["ver registro de auditoría\nGET /api/v1/audit-logs"]
    end

    subgraph GestionProyectos["gestión de proyectos y escaneos"]
        CP["crear / editar proyectos\nPOST·PUT /api/v1/projects"]
        CS["crear escaneos\nPOST /api/v1/scans"]
        UP["subir informe Trivy\nPOST /api/v1/scans/{id}/trivy-report"]
        VS["ver escaneos del proyecto\nGET /api/v1/scans"]
    end

    subgraph GestionVulns["gestión de vulnerabilidades"]
        VV["ver vulnerabilidades\nGET /api/v1/vulnerabilities"]
        AE["actualizar estado\nPATCH /api/v1/vulnerabilities/{id}"]
        FI["filtrar por severidad / CVE"]
    end

    U --> Login & Logout & Pwd
    ADM --> CU & RO & AU
    MAE --> CP & CS & UP & VS
    INS --> VV & AE & FI
```

---

### 4.6 DFD Nivel 0 — Modelo de Contexto

> Compatible con OWASP Threat Dragon. El sistema como caja negra con sus cinco entidades externas y flujos de datos principales.

```mermaid
graph LR
    UE["usuario externo"]
    ADM["administrador\ndel sistema"]
    TS["Trivy Scanner\nherramienta externa"]
    CICD["CI/CD Pipeline\nGitHub Actions"]
    SEC["equipo de\nseguridad"]

    SYS[["VulnCentral\nsistema de gestión\nde vulnerabilidades"]]

    UE -->|"credenciales / solicitudes HTTP"| SYS
    SYS -->|"tokens JWT / datos / reportes"| UE

    ADM -->|"gestión usuarios · asignación roles"| SYS
    SYS -->|"logs de auditoría · confirmaciones"| ADM

    TS -->|"informe JSON Trivy\nPOST /trivy-report"| SYS

    CICD -->|"trigger escaneo\nreportes SAST/DAST"| SYS
    SYS -->|"resultado análisis\nbadges de estado"| CICD

    SEC -->|"actualizar estado vulnerabilidades"| SYS
    SYS -->|"reportes / alertas CVE"| SEC
```

---

### 4.7 DFD Nivel 1 — Desglose Interno

> Cuatro procesos internos (P1–P4) y seis almacenes de datos (D1–D6). Incluye mapeo de amenazas OWASP Threat Dragon.

```mermaid
graph TB
    UE["usuario externo"]
    TS["Trivy Scanner"]

    subgraph Sistema["VulnCentral — procesos internos"]
        P1(["P1\nautenticar\nusuario"])
        P2(["P2\ngestionar entidades\nproyectos / usuarios"])
        P3(["P3\nrecibir reporte\nTrivy JSON"])
        P4(["P4\nnormalizar y persistir\nvulnerabilidades"])
    end

    subgraph Almacenes["almacenes de datos"]
        D1[("D1\nusuarios")]
        D2[("D2\nproyectos")]
        D3[("D3\nescaneos")]
        D4[("D4\nvulnerabilidades")]
        D5[/"D5\ncola AMQP\nRabbitMQ"/]
        D6[/"D6\nvolumen\nreports_data"/]
    end

    UE -->|"email + password"| P1
    P1 -->|"JWT token"| UE
    P1 <-->|"leer usuario\nINSERT auditoría"| D1

    UE -->|"datos proyecto / usuario"| P2
    P2 <-->|"CRUD proyectos"| D2
    P2 <-->|"CRUD usuarios"| D1

    TS -->|"archivo JSON Trivy"| P3
    P3 -->|"guardar JSON"| D6
    P3 -->|"publicar scan_id + ruta"| D5
    P3 -->|"INSERT registro escaneo"| D3
    P3 -->|"HTTP 202 Accepted"| UE

    D5 -->|"consumir mensaje"| P4
    D6 -->|"leer archivo JSON"| P4
    P4 -->|"INSERT vulnerabilidades normalizadas"| D4
    P4 -->|"UPDATE estado escaneo"| D3
```

> **Mapeo de amenazas por proceso — OWASP Threat Dragon:**
>
> | Proceso | Amenaza | Control implementado |
> |---------|---------|---------------------|
> | P1 — Autenticar | Fuerza bruta / Credential Stuffing | Rate limiting por IP: `slowapi` (`RATE_LIMIT_LOGIN=5/minute`) |
> | P2 — Gestionar entidades | IDOR / BOLA — acceso a recursos de otro usuario | `WHERE project_id IN (SELECT ... WHERE user_id = ?)` en cada consulta |
> | P3 — Recibir reporte | Upload malicioso / DoS por archivo masivo | Validación MIME type + `MAX_JSON_BODY_BYTES` (default 10 MiB) |
> | P4 — Normalizar | Path Traversal al leer el volumen | Validación de ruta canónica bajo `REPORTS_BASE_DIR` antes de abrir el archivo |

---

## 5. Seguridad — Capas de Defensa

| Capa | Medidas implementadas |
|------|-----------------------|
| **Red** | Red Docker aislada `vulncentral_net`. CORS con lista explícita de orígenes (`CORS_ORIGINS`). TLS en producción vía balanceador o Nginx. |
| **Aplicación** | JWT HS256 stateless. RBAC granular por rol y caso de uso. Rate limiting (`slowapi`). Validación MIME en uploads. |
| **Datos** | Passwords con bcrypt (passlib). Soft Delete para preservar auditoría. Filtros IDOR a nivel SQL. Migraciones versionadas (Alembic). |
| **Infraestructura** | Docker Secrets para credenciales. Healthchecks en todos los servicios. Límites de memoria por contenedor. |
| **CI/CD — Shift-Left** | Bandit (SAST Python) · Semgrep (análisis estático) · Gitleaks (secretos) · Trivy (scan de imagen) · ZAP Baseline (DAST) · pip-audit · npm audit |

---

## 6. Contrato AMQP — Ingesta de Informes Trivy

**Cola:** `vulncentral` · **Tarea:** `vulncentral.ingest_trivy_json` · **Serialización:** JSON

| Orden | Campo | Tipo | Obligatorio | Descripción |
|-------|-------|------|-------------|-------------|
| 1 | `scan_id` | `int` | Sí | ID del escaneo en `scans.id` (debe existir y no estar soft-deleted) |
| 2 | `file_path` | `str` | Sí | Ruta absoluta del JSON validada bajo `REPORTS_BASE_DIR` |
| 3 | `correlation_id` | `str \| null` | No | UUID para trazas entre API, cola y worker |

**Comportamiento de reintentos:** reintenta ante errores transitorios (DB, red); **no** reintenta `ValueError`, `ValidationError` ni `JSONDecodeError`. El fichero JSON se elimina solo tras commit exitoso.

---

## 7. Gobierno de Migraciones de Base de Datos

1. **Un solo hilo Alembic** en `services/api-gateway/alembic`. No crear carpetas de migración en el worker.
2. **Cambios en tablas compartidas** (`vulnerabilities`, `scans`): revisión conjunta en PR; desplegar API y Worker en la misma ventana si el cambio rompe compatibilidad.
3. **Entorno local:** tras `git pull`, ejecutar `alembic upgrade head` desde el contenedor `api-gateway`.

```bash
# Aplicar migraciones pendientes
docker compose exec api-gateway alembic upgrade head

# Crear nueva migración
docker compose exec api-gateway alembic revision --autogenerate -m "descripcion"

# Revertir última migración
docker compose exec api-gateway alembic downgrade -1
```

---

## 8. Pipeline CI/CD

```yaml
name: VulnCentral CI/CD Pipeline
on: [push, pull_request]

jobs:
  security:
    steps:
      - bandit -r services/api-gateway services/worker -lll   # SAST Python
      - semgrep --config p/python --config p/ci               # análisis estático
      - gitleaks detect --source .                            # detección de secretos
      - pip-audit -r services/api-gateway/requirements.txt    # CVEs Python
      - npm audit --audit-level=critical --prefix services/frontend

  build:
    needs: security
    steps:
      - docker build -t vulncentral-api ./services/api-gateway
      - trivy image --exit-code 1 --severity HIGH,CRITICAL vulncentral-api

  test:
    needs: build
    steps:
      - pytest --cov=app --cov-fail-under=85 --cov-report=xml
      - docker run owasp/zap2docker-stable zap-baseline.py -t http://staging
```
## 9. Ingesta de informe Trivy (asíncrona)

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
---
