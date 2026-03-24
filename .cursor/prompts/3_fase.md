# FASE 3: Implementar autenticación y autorización.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- JWT Authentication
- RBAC usando Depends (FastAPI)
- Poblar las tablas indicadas seeders

## REQUISITOS:
- Login seguro
- Generación de tokens
- Middleware de autenticación
- Sistema de roles:
  - Administrator
  - Master
  - Inspector

IMPLEMENTAR:
- Validación de permisos por endpoint
- Protección contra:
  - Token expirado
  - Token inválido

## SEEDERS 
**ATENCION** El orden que se da para ingresar tanto las tablas como las filas debe respetarse, crea y corre los scripts en el orden exacto que decribo.

Carga datos iniciales (seeders) en la tablas respectivas asi:
- Crear script de seeders en Python
- Poblar automáticamente:

### use_cases

**Row 1**
- name: Gestor usuarios
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 2**
- name: Gestor proyectos
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 3**
- name: Gestor escaneos
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 4**
- name: Gestor vulnerabilidades
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 5**
- name: Gestor logs
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

### roles

**Row 1**
- name: Administrator
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 2**
- name: Master
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 3**
- name: Inspector
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

### permissions

**Row 1**
- role_id: 1
- use_case_id: 1
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 2**
- role_id: 1
- use_case_id: 2
- C: false
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 3**
- role_id: 1
- use_case_id: 3
- C: false
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 4**
- role_id: 1
- use_case_id: 4
- C: false
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 5**
- role_id: 1
- use_case_id: 5
- C: false
- R: true
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()


**Row 6**
- role_id: 2
- use_case_id: 1
- C: false
- R: false
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 7**
- role_id: 2
- use_case_id: 2
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 8**
- role_id: 2
- use_case_id: 3
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 9**
- role_id: 2
- use_case_id: 4
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 10**
- role_id: 2
- use_case_id: 5
- C: false
- R: false
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 11**
- role_id: 3
- use_case_id: 1
- C: false
- R: false
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 12**
- role_id: 3
- use_case_id: 2
- C: false
- R: true
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 13**
- role_id: 3
- use_case_id: 3
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 14**
- role_id: 3
- use_case_id: 4
- C: true
- R: true
- U: true
- D: true
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()

**Row 15**
- role_id: 3
- use_case_id: 5
- C: false
- R: false
- U: false
- D: false
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()


## Crear usuario inicial:

### users
- name: elmero
- email: elmero@admon.com
- password: hasheado("elmero/*-")
- deleted_at: NULL
- created_at: Now()
- updated_at: Now()


## ENTREGABLE:
- Endpoints auth
- Middleware
- RBAC funcional
- Seeders
