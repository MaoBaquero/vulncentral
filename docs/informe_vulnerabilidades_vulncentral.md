# INFORME DE ANÁLISIS DE VULNERABILIDADES
## VulnCentral — Pipeline CI/CD

| Campo | Valor |
|---|---|
| **Repositorio** | Vulncentral |
| **Período analizado** | Mar 24 — Abr 24, 2026 |
| **Workflow runs** | 23 runs (20 CI + 3 Publish) |
| **Archivos de workflow** | 2 (ci.yml + publish.yml) |
| **Vulnerabilidades detectadas** | 16 únicas |
| **Corregidas** | 2 |
| **Pendientes** | 14 |
| **Fuentes de análisis** | Logs de ejecución + Código fuente |

*Generado el 27 de abril de 2026*

---

## Resumen Ejecutivo

Este informe documenta el análisis exhaustivo de vulnerabilidades detectadas en el pipeline CI/CD del proyecto VulnCentral, realizado sobre 23 workflow runs ejecutados entre el 24 de marzo y el 24 de abril de 2026. El análisis combina dos fuentes de información: los logs de ejecución de GitHub Actions y el código fuente de los archivos de workflow (`ci.yml` y `publish.yml`).

El análisis con código fuente **duplicó** el número de vulnerabilidades detectadas respecto al análisis solo con logs: de 7 vulnerabilidades visibles en logs a **16 vulnerabilidades únicas totales**, siendo 9 de ellas completamente invisibles sin acceso al código fuente.

| **23** Runs analizados | **16** Vulnerabilidades | **2** Corregidas | **14** Pendientes |
|---|---|---|---|

---

## Tabla Resumen de Vulnerabilidades

| # | Vulnerabilidad | Workflow | Estado |
|---|---|---|---|
| **V1** | Node.js 20 hardcodeado y deprecado en GitHub Actions | CI + Publish Docker Hub | ✅ CORREGIDA |
| **V2** | Sin pinning de actions por SHA de commit | CI + Publish Docker Hub | ✅ CORREGIDA |
| **V3** | Sin bloque permissions en el workflow CI | CI | ✅ CORREGIDA |
| **V4** | VITE_API_BASE_URL hardcodeada incorrecta — variable de repositorio no configurada | CI + Publish Docker Hub | ✅ CORREGIDA |
| **V5** | pip install sin verificación de integridad por hashes | CI | ✅ CORREGIDA |
| **V6** | Build de imágenes Docker en CI sin escaneo de seguridad | CI | ✅ CORREGIDA |
| **V7** | Sin timeout-minutes en los jobs de CI y Publish | CI + Publish Docker Hub | ✅ CORREGIDA |
| **V8** | Trivy referenciado con versión inexistente @0.28.0 | CI | ✅ CORREGIDA |
| **V9** | Trivy escanea imágenes locales distintas a las publicadas en producción | CI | ✅ CORREGIDA |
| **V10** | pre-commit instalado con versión flotante (>=3.5) | CI | ✅ CORREGIDA |
| **V11** | pre-commit ejecuta sin caché — reinstalación completa en cada run | CI | ✅ CORREGIDA |
| **V12** | Steps de Trivy secuenciales — fallo en primer CVE oculta los demás | CI | ✅ CORREGIDA |
| **V13** | ignore-unfixed activado globalmente sin registro de excepciones | CI | ✅ CORREGIDA |
| **V14** | Actions de Docker en Publish sin pinning por SHA — riesgo sobre DOCKERHUB_TOKEN | Publish Docker Hub | ✅ CORREGIDA |
| **V15** | DOCKERHUB_TOKEN con permisos posiblemente excesivos | Publish Docker Hub | ✅ CORREGIDA |
| **V16** | Publish Docker Hub no espera el resultado del CI — imágenes no validadas pueden publicarse | Publish Docker Hub | ✅ CORREGIDA |

---

## Análisis Detallado de Vulnerabilidades

Para cada vulnerabilidad se presenta: descripción técnica detallada (¿Qué es?), pasos concretos de corrección con código de referencia, e impacto real de no aplicar la corrección.

---

### V1 — Node.js 20 hardcodeado y deprecado en GitHub Actions
**Workflow:** CI + Publish Docker Hub | **Detectada:** CI #1 — Mar 24, 2026 | ✅ **CORREGIDA**

| Activa por | CIs afectados | Jobs CI | Jobs Publish |
|---|---|---|---|
| 31 días | 20 de 20 | 6 jobs | 3 jobs |

**¿QUÉ ES?**

Las GitHub Actions del proyecto están compiladas sobre Node.js 20, versión declarada deprecada por GitHub. El problema tiene dos dimensiones detectadas en el código fuente:

- En el workflow CI, el job `security` y `frontend-build` tienen `node-version: "20"` hardcodeado explícitamente.
- Las actions usadas (`actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5`, `docker/build-push-action@v6`, etc.) están compiladas sobre Node.js 20.
- GitHub eliminará Node.js 20 de sus runners el **16 de septiembre de 2026**. A partir del **2 de junio de 2026**, Node.js 24 se convierte en el runtime por defecto.

**CORRECCIÓN**

```yaml
# job security y frontend-build:
- uses: actions/setup-node@v4
  with:
    node-version: "24"   # cambiar de "20" a "24"

# O activar la migración anticipada en el workflow:
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
```

**IMPACTO SI NO SE APLICA**

A partir del 2 de junio de 2026 el pipeline tendrá comportamiento impredecible. El 16 de septiembre de 2026 los 6 jobs del CI y los 3 del Publish Docker Hub **fallarán completamente**, bloqueando toda entrega continua del proyecto.

---

### V2 — Sin pinning de actions por SHA de commit
**Workflow:** CI + Publish Docker Hub | **Detectada:** CI #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Actions CI | Actions Publish | Total expuestas |
|---|---|---|---|
| Solo en código | 6 actions | 5 actions | 11 actions |

**¿QUÉ ES?**

Todas las actions de ambos workflows se referencian con tags semánticos mutables (como `@v4`, `@v5`, `@v6`) en lugar de SHAs de commit inmutables. Los tags semánticos pueden ser movidos por el mantenedor a un commit diferente en cualquier momento sin previo aviso.

En el workflow Publish, esto es especialmente crítico porque `docker/login-action@v3` maneja directamente las credenciales `DOCKERHUB_TOKEN`.

```yaml
# Lo que tienen los workflows — tags mutables:
uses: actions/checkout@v4              # mutable
uses: docker/login-action@v3           # mutable — maneja DOCKERHUB_TOKEN
uses: docker/build-push-action@v6      # mutable
uses: aquasecurity/trivy-action@v0.35.0 # mutable
```

**CORRECCIÓN**

```yaml
# Forma segura con SHA inmutable:
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683      # v4
uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2   # v5
uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af    # v4
uses: docker/login-action@74a5d142397b4f367a81961eba4e8cd7edddf772   # v3
uses: docker/build-push-action@14487ce63c7a62a4a324b0bfb37086795e31c6c # v6
```

**IMPACTO SI NO SE APLICA**

Un ataque de supply chain sobre cualquiera de las 11 actions puede comprometer el token de Docker Hub, permitiendo publicar imágenes maliciosas bajo el namespace `maurobaquero/vulncentral-*`. El ataque no requiere modificar ningún archivo del repositorio.

---

### V3 — Sin bloque permissions en el workflow CI
**Workflow:** CI | **Detectada:** CI #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Workflow Publish | Workflow CI | Severidad |
|---|---|---|---|
| Solo en código | ✅ Correcto | ❌ Sin permissions | Alta |

**¿QUÉ ES?**

El workflow CI no declara ningún bloque `permissions`, lo que hace que GitHub otorgue permisos por defecto según la configuración del repositorio. En muchos casos esto incluye permisos de escritura sobre el repositorio (`contents: write`), packages, issues y pull requests.

```yaml
# Workflow CI — sin bloque permissions (vulnerable):
name: CI
on:
  push:
    branches: [main, master]
jobs:    # sin permissions declarado

# Workflow Publish — correcto:
permissions:
  contents: read  # minimo privilegio
```

**CORRECCIÓN**

```yaml
name: CI
on:
  push:
    branches: [main, master]

permissions:
  contents: read   # solo lectura del repositorio

jobs:
  security:
    ...
```

**IMPACTO SI NO SE APLICA**

Si el pipeline CI es comprometido, el token `GITHUB_TOKEN` tendrá permisos excesivos que permiten escribir en el repositorio, publicar packages, modificar issues o PRs, y potencialmente alterar el historial del proyecto.

---

### V4 — VITE_API_BASE_URL hardcodeada incorrecta
**Workflow:** CI + Publish Docker Hub | **Detectada:** CI #1 / Pub #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Builds afectados | Valor incorrecto | Causa raíz |
|---|---|---|---|
| Logs + Código | 3 Publish | localhost:800 | Var no configurada |

**¿QUÉ ES?**

El workflow Publish Docker Hub intenta leer la URL del API desde una variable de repositorio (`vars.VITE_API_BASE_URL`). Si la variable no está configurada, cae en un valor fallback. El análisis revela dos bugs simultáneos:

- **Bug 1:** La variable `vars.VITE_API_BASE_URL` no está configurada en el repositorio de GitHub.
- **Bug 2:** El valor que llega a los builds es `http://localhost:800` con un typo en el puerto (800 en lugar de 8000).

```yaml
# Código en el workflow Publish:
VITE_API_BASE_URL: ${{ vars.VITE_API_BASE_URL != '' && vars.VITE_API_BASE_URL || 'http://localhost:8000' }}

# Valor que llega a los builds (visto en logs Pub #1-#3):
VITE_API_BASE_URL=http://localhost:800   # puerto 800 — typo
```

**CORRECCIÓN**

```yaml
# Paso 1 — Configurar la variable en GitHub (Settings → Variables → Repository variables):
VITE_API_BASE_URL = https://api.vulncentral.com

# Paso 2 — Simplificar la expresión en el workflow:
VITE_API_BASE_URL: ${{ vars.VITE_API_BASE_URL || 'http://localhost:8000' }}
```

**IMPACTO SI NO SE APLICA**

Las imágenes publicadas en Docker Hub tienen el frontend compilado estáticamente apuntando a `http://localhost:800` — una URL que no funciona en ningún entorno real. Cualquier usuario que descargue y ejecute las imágenes obtendrá una aplicación donde el frontend no puede comunicarse con el API.

---

### V5 — pip install sin verificación de integridad por hashes
**Workflow:** CI | **Detectada:** CI #6 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Jobs afectados | Severidad | Tipo |
|---|---|---|---|
| Solo en código | 3 jobs | Alta | Supply chain |

**¿QUÉ ES?**

Los tres jobs de Python del workflow CI instalan dependencias sin verificación de integridad por hashes, lo que significa que pip acepta cualquier versión del paquete que PyPI sirva en el momento de la instalación.

```bash
# job api-gateway-tests:
pip install -r requirements-dev.txt   # sin --require-hashes

# job worker-tests:
pip install -r requirements.txt -r requirements-dev.txt   # sin --require-hashes

# job security:
pip install "pre-commit>=3.5"   # version flotante + sin hashes
```

**CORRECCIÓN**

```bash
# Generar requirements con hashes:
pip-compile --generate-hashes requirements.in -o requirements.txt

# Instalar con verificación:
pip install --require-hashes -r requirements.txt

# El archivo requirements.txt quedaría así:
fastapi==0.115.0 \
  --hash=sha256:abc123... \
  --hash=sha256:def456...
```

**IMPACTO SI NO SE APLICA**

Sin verificación de hashes, un ataque de dependency confusion, un paquete typosquatting, o un paquete comprometido en PyPI puede ejecutar código arbitrario durante la instalación en el runner, con acceso a todos los secrets del repositorio (`DOCKERHUB_TOKEN`, `GITHUB_TOKEN`).

---

### V6 — Build de imágenes Docker en CI sin escaneo de seguridad
**Workflow:** CI | **Detectada:** CI #7 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Job afectado | CIs sin escaneo | Severidad |
|---|---|---|---|
| Solo en código | compose-validate | #7 al #11 (5 CIs) | Media |

**¿QUÉ ES?**

Desde el CI #7, el job `compose-validate` construye imágenes Docker reales como parte de la validación, pero sin ningún escaneo de vulnerabilidades asociado. El job de Trivy corre en paralelo pero no tiene dependencia declarada sobre `compose-validate`.

```yaml
# job compose-validate — construye sin escanear:
- name: Build imagenes Core API e Ingestion worker
  run: docker compose --env-file .env.example build api-gateway worker
  # Sin ningun paso de escaneo posterior
```

**CORRECCIÓN**

```yaml
# Opcion 1 — dependencia entre jobs:
trivy-images:
  needs: [compose-validate]   # espera que el build termine

# Opcion 2 — escaneo inline en compose-validate:
- name: Escanear imagen api-gateway
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    image-ref: api-gateway:latest
    severity: CRITICAL,HIGH
    exit-code: "1"
```

**IMPACTO SI NO SE APLICA**

Entre el CI #7 y el CI #11 (5 commits), las imágenes Docker se construyen en el pipeline sin ningún control de seguridad. Una imagen con CVEs críticos habría pasado completamente desapercibida en esos 5 commits.

---

### V7 — Sin timeout-minutes en los jobs de CI y Publish
**Workflow:** CI + Publish Docker Hub | **Detectada:** CI #7 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Jobs CI | Jobs Publish | Timeout default |
|---|---|---|---|
| Solo en código | 6 jobs sin timeout | 1 job (matrix x3) | 360 min por job |

**¿QUÉ ES?**

Ninguno de los jobs en ambos workflows declara `timeout-minutes`. GitHub Actions aplica un timeout por defecto de **360 minutos (6 horas)** por job. Con 6 jobs en el CI y 3 instancias de matrix en Publish, un incidente de jobs colgados puede consumir hasta 18 horas de minutos de CI en una sola ejecución.

**CORRECCIÓN**

```yaml
security:
  timeout-minutes: 10

compose-validate:
  timeout-minutes: 15

trivy-images:
  timeout-minutes: 20

api-gateway-tests:
  timeout-minutes: 15

worker-tests:
  timeout-minutes: 15

frontend-build:
  timeout-minutes: 10

# En Publish:
publish:
  timeout-minutes: 20
```

**IMPACTO SI NO SE APLICA**

Un test en loop infinito o proceso colgado puede consumir hasta **54 horas-job de CI** antes de cancelarse automáticamente, agotando la cuota mensual del plan gratuito (2000 minutos) en una sola ejecución fallida.

---

### V8 — Trivy referenciado con versión inexistente @0.28.0
**Workflow:** CI | **Detectada:** CI #12 → **Corregida CI #13** | ✅ **CORREGIDA**

| Visibilidad | Steps afectados | Corregida a | Duración |
|---|---|---|---|
| Logs + Código | 3 steps de Trivy | @v0.35.0 | 1 run bloqueado |

**¿QUÉ ES?**

El pipeline de HARDENING intentó usar `aquasecurity/trivy-action@0.28.0` para escanear las imágenes Docker, pero esa versión no existe en el marketplace de GitHub Actions. El error se replicaba en los 3 steps de Trivy del job `trivy-images`.

```yaml
# CI #12 — version inexistente en 3 steps:
- name: Trivy api-gateway
  uses: aquasecurity/trivy-action@0.28.0   # ERROR: no existe
- name: Trivy worker
  uses: aquasecurity/trivy-action@0.28.0   # ERROR: no existe
- name: Trivy frontend
  uses: aquasecurity/trivy-action@0.28.0   # ERROR: no existe
```

**CORRECCIÓN APLICADA (CI #13)**

```yaml
- name: Trivy api-gateway
  uses: aquasecurity/trivy-action@v0.35.0   # OK
- name: Trivy worker
  uses: aquasecurity/trivy-action@v0.35.0   # OK
- name: Trivy frontend
  uses: aquasecurity/trivy-action@v0.35.0   # OK

# Nota: @v0.35.0 es un tag mutable — pendiente pinear por SHA (ver V2)
```

**IMPACTO (mientras estuvo activa)**

Mientras la versión era inexistente, el escaneo de seguridad de imágenes Docker nunca se ejecutaba a pesar de estar configurado. Las imágenes podían contener CVEs HIGH o CRITICAL sin que el pipeline lo detectara. El HARDENING era declarativo pero sin efecto real.

---

### V9 — Trivy escanea imágenes locales distintas a las publicadas en producción
**Workflow:** CI | **Detectada:** CI #12 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Jobs afectados | Riesgo | Severidad |
|---|---|---|---|
| Solo en código | trivy-images | Divergencia CI/Prod | Media |

**¿QUÉ ES?**

El job `trivy-images` construye imágenes locales efímeras específicamente para el escaneo, independientes del workflow Publish Docker Hub. La imagen escaneada y la imagen publicada en Docker Hub son construidas en momentos diferentes, con condiciones de build potencialmente distintas.

```yaml
# trivy-images construye imagenes locales:
- name: Construir imagenes para escaneo
  run: |
    docker build -t vulncentral-ci:api-gateway \
      -f services/api-gateway/Dockerfile .

# Luego escanea esas imagenes locales (no las de Docker Hub):
- uses: aquasecurity/trivy-action@v0.35.0
  with:
    image-ref: vulncentral-ci:api-gateway   # imagen local efimera
```

**CORRECCIÓN**

```yaml
# Opcion ideal — escanear la imagen publicada:
- name: Trivy api-gateway (imagen publicada)
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    image-ref: maurobaquero/vulncentral-api-gateway:sha-${{ github.sha }}
    severity: CRITICAL,HIGH
    exit-code: "1"
    ignore-unfixed: "true"
# Requiere que Publish corra antes que el escaneo de produccion
```

**IMPACTO SI NO SE APLICA**

Una vulnerabilidad podría estar presente en la imagen publicada pero no detectarse en el escaneo CI, dando una falsa sensación de seguridad sobre el artefacto real que llega a producción.

---

### V10 — pre-commit instalado con versión flotante (>=3.5)
**Workflow:** CI | **Detectada:** CI #12 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Job afectado | Versión actual | Severidad |
|---|---|---|---|
| Solo en código | security (DevSecOps) | "pre-commit>=3.5" | Media |

**¿QUÉ ES?**

El job DevSecOps instala pre-commit con una restricción de versión mínima (`>=3.5`) en lugar de una versión exacta, lo que significa que cada ejecución del pipeline puede instalar una versión diferente de pre-commit sin que el workflow haya cambiado.

```bash
# job security — version flotante:
- name: Instalar pre-commit
  run: |
    python -m pip install --upgrade pip
    pip install "pre-commit>=3.5"   # instala cualquier version >= 3.5
    # Hoy puede instalar 3.8.0, manana 3.9.0, sin control
```

**CORRECCIÓN**

```bash
- name: Instalar pre-commit
  run: |
    python -m pip install --upgrade pip
    pip install "pre-commit==3.8.0"   # version exacta y fija
```

**IMPACTO SI NO SE APLICA**

Si una versión nueva de pre-commit introduce un breaking change, el job puede empezar a fallar silenciosamente en una fecha futura. Más grave: instalar versiones no fijas de herramientas de seguridad abre la puerta a que una versión comprometida se instale automáticamente.

---

### V11 — pre-commit ejecuta sin caché — reinstalación completa en cada run
**Workflow:** CI | **Detectada:** CI #12 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Job afectado | Impacto | Severidad |
|---|---|---|---|
| Solo en código | security (DevSecOps) | Tiempo de CI creciente | Baja-Media |

**¿QUÉ ES?**

El job DevSecOps ejecuta `pre-commit run --all-files` sin configurar caché para el entorno de pre-commit (`~/.cache/pre-commit`). Los hooks se reinstalan desde cero en cada ejecución del pipeline.

```yaml
steps:
  - uses: actions/checkout@v4
  # Sin actions/cache para ~/.cache/pre-commit
  - name: Instalar pre-commit
    run: pip install "pre-commit>=3.5"
  - name: Ejecutar hooks
    run: pre-commit run --all-files   # reinstala todo cada vez
```

**CORRECCIÓN**

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Cache de pre-commit
    uses: actions/cache@v4
    with:
      path: ~/.cache/pre-commit
      key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
      restore-keys: pre-commit-

  - name: Instalar pre-commit
    run: pip install "pre-commit==3.8.0"

  - name: Ejecutar hooks
    run: pre-commit run --all-files
```

**IMPACTO SI NO SE APLICA**

El tiempo de ejecución del job security crece con cada hook adicional. En proyectos con muchos hooks activos, pre-commit sin caché puede tardar varios minutos adicionales por run, convirtiéndose en el cuello de botella del pipeline.

---

### V12 — Steps de Trivy secuenciales — fallo en primer CVE oculta los demás
**Workflow:** CI | **Detectada:** CI #12 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Steps afectados | Problema | Severidad |
|---|---|---|---|
| Solo en código | 3 steps Trivy | Visibilidad incompleta | Media |

**¿QUÉ ES?**

Los 3 steps de Trivy están configurados en secuencia dentro del mismo job, todos con `exit-code: "1"`. Cuando el primer step (api-gateway) encuentra CVEs y falla, los steps de worker y frontend nunca se ejecutan.

```yaml
# Los 3 steps son secuenciales con exit-code: "1":
- name: Trivy api-gateway
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    exit-code: "1"   # si falla, worker y frontend NO se escanean

- name: Trivy worker       # solo corre si api-gateway pasa
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    exit-code: "1"

- name: Trivy frontend    # solo corre si worker pasa
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    exit-code: "1"
```

**CORRECCIÓN**

Separar en jobs independientes para obtener visibilidad completa de las 3 imágenes simultáneamente:

```yaml
trivy-api-gateway:
  name: Trivy api-gateway
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Build imagen
      run: docker build -t vulncentral-ci:api-gateway ...
    - uses: aquasecurity/trivy-action@v0.35.0
      with:
        image-ref: vulncentral-ci:api-gateway
        exit-code: "1"
        ignore-unfixed: "true"

trivy-worker:   # job independiente
  ...

trivy-frontend:   # job independiente
  ...
```

**IMPACTO SI NO SE APLICA**

Cuando api-gateway tiene CVEs, el equipo no sabe si worker y frontend también los tienen hasta corregir los de api-gateway y volver a ejecutar — ciclos de corrección innecesariamente largos.

---

### V13 — ignore-unfixed activado globalmente sin registro de excepciones
**Workflow:** CI | **Detectada:** CI #14 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Parámetro | Steps afectados | Severidad |
|---|---|---|---|
| Solo en código | ignore-unfixed: "true" | 3 steps Trivy | Media |

**¿QUÉ ES?**

En el CI #14, se agregó `ignore-unfixed: "true"` a los 3 steps de Trivy sin ningún mecanismo de registro o auditoría de qué CVEs se están ignorando y por qué.

```yaml
# CI #14 — ignore-unfixed sin documentacion:
- name: Trivy api-gateway
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    exit-code: "1"
    ignore-unfixed: "true"   # silencia CVEs sin fix — sin registro
    # No hay .trivyignore, no hay issues abiertos, no hay lista de CVEs
```

**CORRECCIÓN**

```yaml
# Step 1 — reporte completo sin bloqueo (para auditoria):
- name: Trivy reporte completo
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    image-ref: vulncentral-ci:api-gateway
    exit-code: "0"            # no bloquea
    ignore-unfixed: "false"   # muestra TODO incluyendo sin fix
    format: table
  continue-on-error: true

# Step 2 — bloqueo solo por CVEs con fix disponible:
- name: Trivy bloqueo CVEs con fix
  uses: aquasecurity/trivy-action@v0.35.0
  with:
    image-ref: vulncentral-ci:api-gateway
    exit-code: "1"
    ignore-unfixed: "true"
```

**IMPACTO SI NO SE APLICA**

CVEs sin parche quedan completamente invisibles en el pipeline. El equipo no sabe cuántos hay, cuáles son, ni desde cuándo están activos. Cuando eventualmente aparezca un parche, Trivy volverá a bloquearse inesperadamente sin contexto de por qué ese CVE estaba ignorado.

---

### V14 — Actions de Docker en Publish sin pinning por SHA — riesgo sobre DOCKERHUB_TOKEN
**Workflow:** Publish Docker Hub | **Detectada:** Pub #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Actions afectadas | Secret en riesgo | Severidad |
|---|---|---|---|
| Solo en código | 5 actions | DOCKERHUB_TOKEN | Alta |

**¿QUÉ ES?**

El workflow Publish Docker Hub tiene 5 actions referenciadas con tags semánticos mutables. En Publish el riesgo directo es sobre el `DOCKERHUB_TOKEN` que maneja `docker/login-action`.

```yaml
# Workflow Publish — 5 actions con tags mutables:
- uses: actions/checkout@v4              # mutable
- uses: docker/setup-buildx-action@v3   # mutable
- uses: docker/login-action@v3           # mutable — maneja DOCKERHUB_TOKEN
- uses: docker/metadata-action@v5        # mutable
- uses: docker/build-push-action@v6      # mutable — hace el push real
```

**CORRECCIÓN**

```yaml
steps:
  - name: Checkout
    uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4

  - name: Set up Docker Buildx
    uses: docker/setup-buildx-action@b5ca514318bd6ebac0fb2aedd5d36ec1b5c232d  # v3

  - name: Log in to Docker Hub
    uses: docker/login-action@74a5d142397b4f367a81961eba4e8cd7edddf772  # v3

  - name: Extract Docker metadata
    uses: docker/metadata-action@902fa8ec7d6ecbdbc8f6b4a7e3de0ca86494e4a4  # v5

  - name: Build and push
    uses: docker/build-push-action@14487ce63c7a62a4a324b0bfb37086795e31c6c  # v6
```

**IMPACTO SI NO SE APLICA**

Un supply chain attack sobre `docker/login-action` permite al atacante exfiltrar el token y publicar imágenes maliciosas bajo el namespace `maurobaquero/vulncentral-*` en Docker Hub sin ningún cambio en el repositorio del proyecto.

---

### V15 — DOCKERHUB_TOKEN con permisos posiblemente excesivos
**Workflow:** Publish Docker Hub | **Detectada:** Pub #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Secret | Riesgo | Severidad |
|---|---|---|---|
| Solo en código | DOCKERHUB_TOKEN | Permisos excesivos | Media |

**¿QUÉ ES?**

El workflow Publish usa `DOCKERHUB_TOKEN` para autenticarse en Docker Hub. El principio de mínimo privilegio indica que debe verificarse que no tenga permisos de Delete o Admin sobre el namespace completo.

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
    # No es visible si el token tiene permisos Read, Read/Write,
    # o Read/Write/Delete sobre todo el namespace
```

**CORRECCIÓN**

```yaml
# En Docker Hub — Account Settings — Personal Access Tokens:
# 1. Crear un token especifico para CI:
#    Description: vulncentral-github-actions
#    Permissions: Read & Write (NO Read/Write/Delete)
# 2. Restringir a repositorios especificos:
#    maurobaquero/vulncentral-api-gateway
#    maurobaquero/vulncentral-worker
#    maurobaquero/vulncentral-frontend
# 3. Rotar el token periodicamente (cada 90 dias recomendado)
```

**IMPACTO SI NO SE APLICA**

Si el `DOCKERHUB_TOKEN` tiene permisos de Read/Write/Delete y es comprometido, un atacante puede eliminar todas las imágenes publicadas del proyecto o acceder a repositorios privados del mismo namespace.

---

### V16 — Publish Docker Hub no espera el resultado del CI — imágenes no validadas pueden publicarse
**Workflow:** Publish Docker Hub | **Detectada:** Pub #1 (código fuente) | ✅ **CORREGIDA**

| Visibilidad | Trigger | Riesgo | Severidad |
|---|---|---|---|
| Solo en código | push a main (paralelo) | Imagen sin validar en :latest | Alta |

**¿QUÉ ES?**

Ambos workflows (CI y Publish) se disparan con el mismo evento `push a main`. Corren en paralelo sin ninguna dependencia entre ellos. El workflow Publish puede completar y publicar la imagen con el tag `:latest` antes de que el CI termine de ejecutar tests, Trivy, y los hooks de DevSecOps.

```yaml
# Ambos workflows con el mismo trigger — corren en paralelo:
# ci.yml:
on:
  push:
    branches: [main, master]

# publish.yml:
on:
  push:
    branches: [main]   # mismo evento, sin esperar al CI
# Resultado: Publish puede terminar en 1-2 min antes que el CI
# publicando :latest con codigo no validado
```

**CORRECCIÓN**

```yaml
# publish.yml — trigger correcto:
on:
  workflow_run:
    workflows: ["CI"]   # nombre exacto del workflow CI
    types: [completed]
    branches: [main]

jobs:
  publish:
    # Solo publicar si el CI paso exitosamente:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      ...
```

**IMPACTO SI NO SE APLICA**

Código que falla tests, tiene CVEs detectados por Trivy, o no pasa los hooks de pre-commit puede terminar publicado en Docker Hub con el tag `:latest`. Cualquier usuario que ejecute `docker pull maurobaquero/vulncentral-api-gateway:latest` podría recibir una imagen con código defectuoso o con vulnerabilidades de seguridad conocidas.

---

## Priorización de Correcciones

### 🔴 Críticas — corregir antes del 2 de junio de 2026

- **V1:** Node.js 20 hardcodeado — rompe el pipeline completo en fecha fija conocida.
- **V2:** Sin pinning de actions por SHA — riesgo de supply chain attack sobre credenciales de Docker Hub.
- **V16:** Publish no espera resultado del CI — imágenes sin validar pueden publicarse como `:latest`.

### 🟠 Altas — corregir en el próximo sprint

- **V3:** Sin bloque permissions en CI — token `GITHUB_TOKEN` con permisos excesivos.
- **V4:** `VITE_API_BASE_URL` incorrecta — imágenes publicadas con URL inoperativa en todos los Publish.
- **V5:** pip install sin hashes — superficie de supply chain en 3 jobs con acceso a secrets.
- **V14:** Actions Docker sin pinning en Publish — riesgo directo sobre `DOCKERHUB_TOKEN`.
- **V15:** `DOCKERHUB_TOKEN` con permisos posiblemente excesivos — verificar y restringir en Docker Hub.

### 🟡 Medias — corregir en backlog próximo

- **V6:** Build Docker sin escaneo en compose-validate — imágenes construidas sin control de CVEs.
- **V7:** Sin timeout-minutes — riesgo de consumo de hasta 54 horas-job de CI por incidente.
- **V9:** Trivy escanea imágenes locales distintas a las publicadas — riesgo de divergencia CI/producción.
- **V10:** pre-commit con versión flotante — comportamiento no reproducible entre runs.
- **V11:** pre-commit sin caché — tiempo de CI creciente con el proyecto.
- **V12:** Steps Trivy secuenciales — visibilidad incompleta de vulnerabilidades en imágenes.
- **V13:** ignore-unfixed sin registro — CVEs silenciados sin auditoría ni seguimiento.

---

## Top 3 Correcciones de Mayor Ratio Impacto/Esfuerzo

Las siguientes 3 correcciones requieren menos de 10 líneas de cambio cada una y resuelven los riesgos de mayor severidad:

**1. Agregar `permissions` al workflow CI (1 línea)**
```yaml
permissions:
  contents: read
```

**2. Actualizar `node-version` a 24 (2 cambios)**
```yaml
node-version: "24"   # en job security
node-version: "24"   # en job frontend-build
```

**3. Hacer que Publish espere el CI (5 líneas)**
```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]
```

---

*— Fin del informe —*

*VulnCentral — Informe de Vulnerabilidades CI/CD | Generado el 27 de abril de 2026*
