# FASE 1: Generar estructura base del proyecto.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- Crear estructura completa de carpetas según especificación
- Crear docker-compose.yml funcional
- Configurar servicios:
  - api-gateway
  - worker
  - frontend
  - postgres
  - rabbitmq

## REQUISITOS:
- Incluir límites de memoria en docker-compose
- Definir volumen compartido para reports (/app/data/reports)
- Configurar variables de entorno (.env)
- Crear Dockerfile para cada servicio


## ESPECIFICACIONES 


### Estructura del Repositorio

```
vulncentral/
├── LICENSE
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── services/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── src/
│   │
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   ├── app/
│   │   └── tests/
│   │
│   ├── worker/
│   │   ├── Dockerfile
│   │   └── tasks/
│
├── orchestration/
│   ├── docker-swarm/
│   │   └── stack.yml
│   └── k8s/
│       ├── deployments/
│       ├── services/
│       └── ingress.yaml
│
├── infrastructure/
│   ├── terraform/
│   └── ansible/
│
├── monitoring/ (opcional)
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
│
├── .github/
│   └── workflows/
│
└── docs/
```

---

### Como debes manejar el docker-compose.yml 
Cuando estes creando el archivo docker-compose.yml incluye límites de memoria (deploy.resources.limits.memory) para cada servicio, optimizándolos para un entorno de desarrollo con recursos limitados.

### Componentes que debes utilizar
- Frontend: React (SPA)
- Backend: FastAPI
- API Gateway: FastAPI (Python)
- Worker: Procesamiento asíncrono (Celery)
- Base de datos: PostgreSQL
- Broker: RabbitMQ
- Autenticación: JWT

## **ATENCION:** NO generar lógica de negocio todavía.

## ENTREGABLE:
- Estructura completa
- docker-compose.yml
- Dockerfiles
- .env.example