<!-- 
4.4 Manual de Despliegue y Operación
Instrucciones detalladas para desplegar la aplicación desde cero en un entorno limpio:
- Requisitos previos del servidor o máquina de destino
- Variables de entorno necesarias y su gestión segura
- Pasos de configuración de infraestructura (IaC)
- Verificación del despliegue correcto
- Resolución de problemas comunes (troubleshooting) 
-->

<img src="../IMG/LogoVC-horizontal.png" alt="VulnCentral" width="420"/> <br/>

# 📘 Manual de Despliegue y Operación
## 📌 Este manual le permite:

✔ Desplegar VulnCentral desde cero <br>
✔ Validar funcionamiento completo <br>
✔ Operar el sistema correctamente <br>
✔ Resolver problemas comunes <br>

---

## 1. 🧩 Requisitos previos del servidor o máquina de destino

Antes de iniciar el despliegue, asegúrate de contar con un entorno limpio con los siguientes requisitos:

### 🔧 Software obligatorio

| Componente          | Versión recomendada | Verificación             |
| ------------------- | ------------------- | ------------------------ |
| Docker Engine       | ≥ 24.x              | `docker --version`       |
| Docker Compose (v2) | ≥ 2.x               | `docker compose version` |
| Git                 | Última estable      | `git --version`          |

### 💻 Requisitos de hardware mínimos

* CPU: 2 núcleos
* RAM: 4 GB (recomendado 8 GB)
* Disco: 10 GB libres

### 🌐 Requisitos de red

* Puertos disponibles:

  * `8080` → Frontend
  * `8000` → API Gateway
  * `5432` → PostgreSQL (interno)
  * `5672` → RabbitMQ (interno)
  * `15672` → RabbitMQ UI
  * `5050` → pgAdmin (opcional)

⚠️ Verifica que ningún puerto esté ocupado:

```bash
netstat -tulnp | grep 8080
```

---

## 2. 🔐 Variables de entorno necesarias y su gestión segura

Las variables de entorno se definen en el archivo `.env`.

### 📄 Paso 1: Crear archivo de configuración

```bash
cp .env.example .env
```

---

### 🔑 Variables críticas

| Variable                | Descripción              |
| ----------------------- | ------------------------ |
| `POSTGRES_USER`         | Usuario de base de datos |
| `POSTGRES_PASSWORD`     | Contraseña segura        |
| `POSTGRES_DB`           | Nombre de la BD          |
| `JWT_SECRET`            | Clave secreta JWT        |
| `CELERY_BROKER_URL`     | URL de RabbitMQ          |
| `CELERY_RESULT_BACKEND` | Backend de resultados    |
| `VITE_API_BASE_URL`     | URL pública del API      |
| `MAX_JSON_BODY_BYTES`   | Tamaño máximo de carga   |

---

### 🔒 Buenas prácticas de seguridad

* ❌ NO subir `.env` a Git
* ✅ Usar contraseñas fuertes (mínimo 12 caracteres)
* ✅ Rotar `JWT_SECRET` en producción
* ✅ Usar herramientas como:

  * Docker Secrets
  * Vault (HashiCorp)
  * Variables de entorno del sistema

Ejemplo seguro:

```bash
JWT_SECRET=7f8a9c!Xz_92#SecureKey
POSTGRES_PASSWORD=S3gur0_P4ss!
```

---

## 3. 🏗️ Pasos de configuración de infraestructura (IaC)

La infraestructura está definida mediante **Docker Compose (Infraestructura como Código)**.

---

### 📦 Paso 1: Clonar repositorio

```bash
git clone <REPO_URL>
cd vulncentral
```

---

### ⚙️ Paso 2: Configurar entorno

```bash
cp .env.example .env
nano .env
```

---

### 🚀 Paso 3: Construir y levantar servicios

```bash
docker compose up --build -d
```

---

### 📊 Servicios desplegados

| Servicio    | Descripción             |
| ----------- | ----------------------- |
| frontend    | Interfaz web            |
| api-gateway | Backend FastAPI         |
| worker      | Procesamiento asíncrono |
| postgres    | Base de datos           |
| rabbitmq    | Cola de mensajes        |
| pgadmin     | Administración BD       |

---

### 🗄️ Paso 4: Ejecutar migraciones

```bash
docker compose exec api-gateway alembic upgrade head
```

---

### 👤 Paso 5: Cargar datos iniciales

```bash
docker compose exec api-gateway python -m app.scripts.seed
```

---

### 🧠 Paso 6: Verificar estado de contenedores

```bash
docker compose ps
```

Todos deben aparecer como:

```
running / healthy
```

---

## 4. ✅ Verificación del despliegue correcto

Una vez desplegado el sistema, validar cada componente:

---

### 🌐 Acceso a servicios

| Servicio | URL                                                          |
| -------- | ------------------------------------------------------------ |
| Frontend | [http://localhost:8080](http://localhost:8080)               |
| API      | [http://localhost:8000/health](http://localhost:8000/health) |
| Swagger  | [http://localhost:8000/docs](http://localhost:8000/docs)     |
| RabbitMQ | [http://localhost:15672](http://localhost:15672)             |
| pgAdmin  | [http://localhost:5050](http://localhost:5050)               |

---

### 🔍 Validación API

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{"status": "ok"}
```

---

### 🔐 Validación autenticación

```bash
curl -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=elmero%40admon.com&password=elmero%2F%2A-"
```

---

### 📡 Validación worker (RabbitMQ)

1. Ingresar a RabbitMQ
2. Ver cola `vulncentral`
3. Verificar mensajes encolados

---

### 🗄️ Validación base de datos

Conectarse vía pgAdmin:

* Host: `postgres`
* Puerto: `5432`
* Usuario: según `.env`

---

## 5. 🛠️ Resolución de problemas comunes (Troubleshooting)

---

### ❌ Error: puerto en uso

```
bind: address already in use
```

✔ Solución:

```bash
docker compose down
```

Cambiar puerto en `.env`:

```bash
FRONTEND_PORT=8081
```

---

### ❌ Error: contenedor detenido

```bash
docker logs <container_id>
```

Problemas comunes:

* Variables mal configuradas
* DB no disponible
* Migraciones no ejecutadas

---

### ❌ Error: API no responde

✔ Verificar:

```bash
docker compose ps
docker compose logs api-gateway
```

✔ Reiniciar servicio:

```bash
docker compose restart api-gateway
```

---

### ❌ Error: fail to fetch (frontend)

Causa: problema de CORS o URL incorrecta

✔ Solución:

* Verificar `.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

* Reiniciar:

```bash
docker compose up -d --force-recreate frontend api-gateway
```

---

### ❌ Error: worker no procesa tareas

✔ Verificar logs:

```bash
docker logs vulncentral-ingestion-worker
```

✔ Verificar conexión RabbitMQ:

```bash
docker compose exec worker ping rabbitmq
```

---

### ❌ Error: migraciones fallan

✔ Solución:

```bash
docker compose exec api-gateway alembic downgrade base
docker compose exec api-gateway alembic upgrade head
```

---

### ❌ Error: base de datos no conecta

✔ Validar variables:

```bash
POSTGRES_HOST=postgres
```

✔ Reiniciar:

```bash
docker compose restart postgres
```

---

## 🔄 Operación básica del sistema

### ▶️ Iniciar servicios

```bash
docker compose up -d
```

### ⏹️ Detener servicios

```bash
docker compose down
```

### 🔁 Reiniciar

```bash
docker compose restart
```

---

## 🔐 Recomendaciones finales de seguridad

* Cambiar credenciales por defecto
* Usar HTTPS en producción
* No exponer RabbitMQ ni PostgreSQL
* Implementar firewall (ej: UFW)
* Usar backups de base de datos





