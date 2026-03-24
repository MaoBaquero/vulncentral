# FASE 5: Implementar Worker con Celery.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- Procesar JSON de Trivy
- Normalizar vulnerabilidades
- Guardar en DB

## REQUISITOS:
- Leer archivo desde volumen compartido
- Recibir:
  - scan_id
  - file_path

## TRANSFORMACIÓN:
- Mapear campos JSON → DB

## SEGURIDAD:
- Validar existencia del archivo
- Manejo de errores robusto

## PROCESO DE REPORTES EN EL WORKER
Procesara inicialmente reportes de Trivy en JSON

**Estructura Principal del JSON de Trivy**

El archivo se organiza principalmente bajo la clave Results, que contiene una lista de los diferentes "objetivos" (targets) analizados (como una imagen Docker o un archivo requirements.txt).


- SchemaVersion: Indica la versión del formato del reporte.
- ArtifactName: El nombre de la imagen o archivo analizado.
- Results: Un arreglo donde cada objeto representa un hallazgo técnico:
  - Target: El archivo o recurso específico donde se halló el problema.
  - Type: El tipo de escaneo (ej. debian, pip, config).
  - Vulnerabilities: Una lista de objetos con el detalle técnico de cada falla.

**Ejemplo de un Hallazgo (Vulnerability)**

Este es el bloque que tu Worker deberá procesar y normalizar para guardarlo en la tabla Vulnerabilities:

<pre>
JSON
{
  "VulnerabilityID": "CVE-2023-12345",
  "PkgName": "openssl",
  "InstalledVersion": "1.1.1t-r0",
  "FixedVersion": "1.1.1u-r0",
  "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2023-12345",
  "Title": "Escalamiento de privilegios en OpenSSL",
  "Description": "Una vulnerabilidad detectada en el manejo de certificados...",
  "Severity": "HIGH",
  "Status": "fixed"
}
</pre>

## Mapeo hacia VulnCentral

El Worker de Celery debe realizar la siguiente transformación:

| Campo en JSON de Trivy | Campo en DB VulnCentral | Acción del Worker |
|---|---|---|
| VulnerabilityID | cve | Extraer el código (ej. CVE-202X-XXXX). |
| Title | title | Título breve de la vulnerabilidad. |
| Description | description | Texto descriptivo del hallazgo. |
| Severity | severity | Mapear a Enums (LOW, MEDIUM, HIGH, CRITICAL). |
| PkgName / Target | file_path | Indicar qué paquete o archivo está afectado, |
| (Generado) | status | Iniciar por defecto en OPEN. |

---

**ATENCION:**
Ten en cuenta que para poder que el worker cargue una vulnerabilidad leida del JSON enviado, debe pasársele también el id del scan, al cual se esta cargando la vulnerabilidad.

## Gestión de Archivos y "Storage"
Configura el flujo de datos de la siguiente manera: Cuando el API Gateway reciba un reporte JSON, debe almacenarlo en un volumen de Docker compartido (ej. /app/data/reports). Una vez guardado, el API enviará un mensaje a RabbitMQ que contenga únicamente el scan_id y la ruta absoluta del archivo. El Worker, al recibir la tarea, leerá el archivo desde esa ruta compartida para iniciar la normalización

**TEN EN CUENTA:**
- Actualice el archivo docker-compose.yml para incluir el volumen compartido entre los servicios api-gateway y worker.
- **Debes Definir una política** de limpieza para borrar los archivos JSON del volumen una vez que el Worker confirme que los datos están en la base de datos PostgreSQL y ponla en el programa


---

## EXTRA:
- Eliminar archivo después de procesar

## ENTREGABLE:
- tasks.py
- lógica completa de procesamiento