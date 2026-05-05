<div align="center">

<img src="./IMG/LogoVC-horizontal.png" alt="VulnCentral" width="420"/>

<br/><br/>

### Plataforma DevSecOps para la Centralización y Gestión de Vulnerabilidades


[![Version](https://img.shields.io/badge/version-2.0.0-blue?style=flat-square)](https://github.com/MaoBaquero/vulncentral/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-compose%20v2-2496ED?style=flat-square&logo=docker)](https://docs.docker.com/compose/)
[![OWASP](https://img.shields.io/badge/security-OWASP%20Top%2010-red?style=flat-square)](https://owasp.org/www-project-top-ten/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](./LICENSE)

**UNIMINUTO · Especialización en Ciberseguridad · Seguridad Entornos Cloud DevOps**

</div>

---

## Descripción del Proyecto


**VulnCentral** es una plataforma diseñada para actuar como **capa de agregación y normalización centralizada** de vulnerabilidades de seguridad. Permite a equipos de seguridad y desarrollo catalogar, rastrear y gestionar vulnerabilidades en sus aplicaciones y sistemas, con un enfoque particular en el procesamiento asíncrono de informes de escaneo **Trivy**.

### Propósito principal

- **Centralizar** la gestión de vulnerabilidades detectadas en diferentes entornos y herramientas
- **Automatizar** el procesamiento de informes de seguridad (Trivy JSON) mediante un pipeline asíncrono
- **Controlar el acceso** con un sistema RBAC granular de cuatro roles: Administrador, Maestro, Inspector y Usuario
- **Facilitar la remediación** con seguimiento de estado por vulnerabilidad y trazabilidad completa
- **Auditar** todas las acciones del sistema con registro inmutable de eventos
- **Integrar** prácticas Shift-Left en pipelines CI/CD con escaneo automático en cada commit



### 🚀 GUÍA RÁPIDA DE INSTALACIÓN

- ### → **[Leer Guia de instalacion Guihub](docs/Inicio_Rapido.md)**
- ### → **[Leer Guia de instalacion Dockerhub](docs/DockerHubPL.md)**

---
## Documentacion Técnica

### Flujo de procesamiento asíncrono

```
Usuario → POST /scans/{id}/trivy-report → API valida + guarda JSON → publica en RabbitMQ
                                                      ↓
                                              HTTP 202 Accepted (inmediato)
                                                      ↓
                                     Celery Worker consume mensaje → parsea JSON
                                                      ↓
                                     Normaliza vulnerabilidades → INSERT en PostgreSQL
```

> El API nunca bloquea al cliente. Responde en milisegundos mientras el Worker procesa en segundo plano.

---

## Tecnologías Empleadas

| Categoría | Tecnología | Versión | Rol en VulnCentral |
|-----------|------------|---------|-------------------|
| **Frontend** | React + Vite + React Router | 18.x / Node 20 | SPA dinámico servido por Nginx. RBAC oculta elementos según rol |
| **API Backend** | FastAPI + Pydantic | Python 3.12 / 0.104+ | Gateway asíncrono ASGI. Pydantic valida el esquema Trivy en tiempo de ejecución |
| **Worker** | Celery | 5.3+ | Procesamiento asíncrono de informes. Reintentos automáticos con backoff exponencial |
| **Message Broker** | RabbitMQ | 3.13 management-alpine | Cola AMQP persistente. Solo transmite `scan_id` + `ruta` (no el payload JSON completo) |
| **Base de datos** | PostgreSQL + SQLAlchemy + Alembic | 16 Alpine / 2.x | Integridad ACID. Migraciones versionadas. Paquete ORM compartido `vulncentral-db` |
| **Autenticación** | JWT + passlib + slowapi | HS256 | Auth stateless. bcrypt para passwords. Rate limiting en `/auth/login` |
| **Proxy / Static** | Nginx | Alpine | Sirve el SPA y actúa como reverse proxy hacia el API |
| **Containerización** | Docker + Docker Compose | Engine 20.10+ / Compose v2 | Stack reproducible con healthchecks y límites de memoria por servicio |
| **Orquestación** | Docker Swarm / Kubernetes | — | Alta disponibilidad y escalado horizontal en producción |
| **CI/CD** | GitHub Actions | — | Pipeline: Bandit (SAST) → Semgrep → Gitleaks → Trivy → pytest → ZAP (DAST) |
| **IaC** | Terraform / Ansible | — | Infraestructura como código para entornos reproducibles |
| **Pre-commit** | Gitleaks + Semgrep + Bandit + pip-audit | v8.24.2 / v1.156.0 / 1.8.3 | Seguridad Shift-Left: mismos controles que CI/CD en local antes del commit |

### Servicios del stack Docker Compose

| Contenedor | Imagen | Puerto host | Memoria límite |
|------------|--------|-------------|----------------|
| `vulncentral-core-api` | Build local | `8000` | 384 MB |
| `vulncentral-ingestion-worker` | Build local | — | 384 MB |
| `vulncentral-frontend` | Build local | `8080` | 128 MB |
| `vulncentral-postgres` | postgres:16-alpine | `5432` | 512 MB |
| `vulncentral-rabbitmq` | rabbitmq:3.13-management-alpine | `5672` / `15672` | 512 MB |
| `vulncentral-pgadmin` | dpage/pgadmin4:8 | `5050` | 384 MB |

---

## Inicio Rápido (Quick Start)

### Prerrequisitos

| Requisito | Verificación | Versión mínima |
|-----------|-------------|----------------|
| Git | `git --version` | cualquier versión |
| Docker Engine | `docker --version` | 20.10+ |
| Docker Compose v2 | `docker compose version` | 2.0+ |
| RAM disponible | — | 4 GB (8 GB recomendado) |
| Disco libre | — | ~3 GB para imágenes |

> **Opcional** (solo si desarrollas fuera de Docker): Python 3.12 y Node.js 20.

---

## Pipeline CI/CD (DevSecOps)

Cada `push` o `pull_request` ejecuta automáticamente:

```
[security]          [build]              [test]
Bandit (SAST)   →   docker build    →   pytest + coverage
Semgrep         →   trivy image     →   ZAP baseline (DAST)
Gitleaks        →
pip-audit       →
npm audit       →
```

Los mismos controles están disponibles localmente con `pre-commit`:

```bash
# Instalar hooks
pip install pre-commit && pre-commit install

# Ejecutar manualmente sobre todos los archivos
pre-commit run --all-files
```
Resumen Ejecutivo

Este informe documenta el análisis exhaustivo de vulnerabilidades detectadas en el pipeline CI/CD del proyecto VulnCentral, realizado sobre 23 workflow runs ejecutados

→ **[Ver detalles de informe](docs/informe_vulnerabilidades_vulncentral.md)**
---

## Documentación del Proyecto

VulnCentral cuenta con documentación técnica completa organizada en manuales especializados. Cada uno está pensado para un perfil distinto — desde el usuario final hasta el equipo de infraestructura.

---

### Manual de Arquitectura

> ¿Quieres entender cómo está construido VulnCentral por dentro?

El manual de arquitectura describe en detalle el patrón de **microservicios asíncronos**, las decisiones de diseño (Choreography Saga, Proxy de Referencia, Defense in Depth), la justificación de cada componente y los 7 diagramas UML completos: Componentes, Despliegue, Secuencia de autenticación, Secuencia de ingesta Trivy, Casos de Uso RBAC, DFD Nivel 0 y DFD Nivel 1 con mapeo de amenazas OWASP.

→ **[Leer Manual de Arquitectura](docs/manual-arquitectura.md)**

---

### Manual de Desarrollo

> ¿Vas a contribuir al proyecto o levantar el entorno local?

El manual de desarrollo cubre paso a paso la configuración del entorno, cómo ejecutar cada servicio en modo desarrollo, cómo correr las pruebas unitarias y de integración con cobertura, y cómo contribuir correctamente siguiendo la estrategia de ramas Git, la convención de commits y el proceso de revisión de Pull Requests.

→ **[Leer Manual de Desarrollo](docs/manual-desarrollo.md)**

---

### Manual de Despliegue y Operación

> ¿Necesitas llevar VulnCentral a producción o a un entorno limpio?

El manual de despliegue detalla los requisitos de hardware y software del servidor, la gestión segura de variables de entorno, los pasos de configuración de infraestructura con Docker Compose (IaC), la verificación del despliegue correcto y la resolución de los problemas más comunes.

→ **[Leer Manual de Despliegue](docs/Manual.de.Despliegue.md)**

---

### Manual de Seguridad

> ¿Quieres conocer el modelo de amenazas y cómo se gestionan las vulnerabilidades?

El manual de seguridad describe el modelo de amenazas del sistema (activos, actores, vectores y controles), explica cómo están configuradas e integradas las herramientas DevSecOps (Trivy, ZAP, Gitleaks, Bandit), enseña a interpretar sus reportes, define el proceso de gestión de vulnerabilidades con SLA por severidad y establece la política de divulgación responsable.

→ **[Leer Manual de Seguridad](docs/Manual.de.Seguridad.md)**

---

### Manual de Usuario

> ¿Eres usuario final y quieres aprender a usar la plataforma?

El manual de usuario guía paso a paso el uso completo de VulnCentral: inicio de sesión, gestión de proyectos y escaneos, carga de informes Trivy, revisión de vulnerabilidades, auditoría de acciones y control de acceso según rol. Incluye el flujo recomendado de trabajo y los errores más frecuentes con su solución.

→ **[Leer Manual de Usuario](docs/Manual_de_Usuario.md)**

---

---

### Informe tecnico


VulCentral nace como respuesta a esta problemática: una plataforma única que consolida, normaliza y facilita la gestión del ciclo de vida de las vulnerabilidades. El presente informe técnico detalla su arquitectura, funcionalidades clave y los resultados obtenidos durante su implementación.

→ **[Leer Informe tecnico](docs/Informe_Técnico_VulnCentral.md)**

---


### Modelado de Amenazas


Este documento cubre el modelado de amenazas de los **seis componentes principales** de VulnCentral y los flujos de datos entre ellos, aplicando la metodología STRIDE para identificar, clasificar y mitigar amenazas de seguridad.

→ **[Leer detalles Modelado de Amenazas](docs/modelado-amenazas.md)**

---

## Autores

| Nombre | Institución |
|--------|-------------|
| Ing. Argel Ochoa Ronald David | UNIMINUTO — Especialización en Ciberseguridad |
| Ing. Baquero Soto Mauricio | UNIMINUTO — Especialización en Ciberseguridad |
| Ing. Buitrago Guiot Óscar Javier | UNIMINUTO — Especialización en Ciberseguridad |
| Ing. Estefanía Naranjo Novoa | UNIMINUTO — Especialización en Ciberseguridad |

---

## Licencia

Este proyecto está distribuido bajo la licencia **MIT**. Ver el archivo [LICENSE](./LICENSE) para más detalles.

---

<div align="center">
<img src="./IMG/LogoVC-horizontal.png" alt="VulnCentral" width="200"/>
<br/>
<sub>VulnCentral · UNIMINUTO · Especialización en Ciberseguridad · Seguridad Entornos Cloud DevOps</sub>
</div>
