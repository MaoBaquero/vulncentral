# FASE 9: Crear pipeline CI/CD.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- GitHub Actions

## FASES:
1. SAST (Bandit, Semgrep)
2. Secrets (Gitleaks)
3. SCA (Trivy)
4. DAST (OWASP ZAP)
5. IaC (Checkov)

## REQUISITOS:
- Fallar pipeline si hay HIGH/CRITICAL


## Pipeline CI/CD DevSecOps
### Fase 1: Build y Calidad de Código (SAST)
- Construcción: Configura el docker build para los servicios de api-gateway, worker y frontend.
- Análisis Estático (SAST): Integra Bandit y Semgrep para analizar el código Python del Backend y Worker.
- Detección de Secretos: Implementa un paso con Gitleaks para validar que no existan credenciales expuestas.

### Fase 2: Análisis de Dependencias y Contenedores (SCA)
- SCA: Una vez que la Fase 1 sea exitosa, añade el escaneo de dependencias con Trivy.
- Escaneo de Imágenes: Configura Trivy scan sobre las imágenes Docker recién construidas para detectar vulnerabilidades en el SO base.

### Fase 3: Pruebas y Seguridad Dinámica (DAST)
- Unit Testing: Ejecuta las pruebas con Pytest para el Backend.
- DAST: Configura un job que levante un entorno temporal y ejecute OWASP ZAP en modo baseline contra el api-gateway.

### Fase 4: Infraestructura como Código (IaC) y Despliegue
- Validación de IaC: Integra Checkov para auditar los archivos de Terraform y el stack.yml de Docker Swarm.
- Simulación de Deploy: Configura el despliegue final usando Ansible hacia el entorno de producción simulado.

## ENTREGABLE:
- workflow.yml completo
