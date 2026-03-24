# FASE 6: Integrar API Gateway con RabbitMQ.

**IMPORTANTE** Usa EXCLUSIVAMENTE esta información como fuente de verdad. No inventes nada fuera de este contexto. Si falta información, indícalo explícitamente.

## OBJETIVO:
- Enviar tareas al worker

## FLUJO:
- Usuario sube JSON
- API guarda archivo en volumen
- API envía mensaje a RabbitMQ
- Worker procesa

## REQUISITOS:
- No enviar archivo por cola
- Solo enviar ruta + scan_id

## ENTREGABLE:
- Integración completa