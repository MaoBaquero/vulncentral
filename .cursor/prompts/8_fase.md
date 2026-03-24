# FASE 8: Endurecimiento de seguridad.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
Implementar controles de seguridad alineados con OWASP WSTG y OWASP Top 10.

## IMPLEMENTAR:
- Validación y sanitización de entradas
- Protección contra IDOR
- Validación de JWT (expiración, firma)
- Rate limiting
- Validación de MIME type y tamaño de archivos
- Prevención de path traversal
- Logging seguro (sin datos sensibles)
- Auditoría de acciones críticas

## REGLA:
No implementar seguridad superficial. Cada control debe ser funcional y aplicado en el código.