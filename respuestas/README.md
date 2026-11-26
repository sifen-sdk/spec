# respuestas

**Propósito.** Los códigos de respuesta de SIFEN, clasificados, para que todos los SDK los interpreten igual y
el sistema emisor sepa qué hacer con cada uno.

**Estado.** Sin datos. Se carga en la fase 1.

## Formato previsto

Cada código lleva:

| Dato | Descripción |
|---|---|
| `codigo` | El código que devuelve SIFEN |
| `servicio` | Servicio que lo devuelve (recepción, lote, consulta de lote, consulta de documento, consulta de RUC, eventos) |
| `mensaje` | El texto oficial |
| `clase` | `aprobacion`, `aprobacion_con_observacion`, `rechazo`, `en_proceso`, `transitorio` o `bloqueo` |
| `accion` | Qué puede hacer el emisor: corregir y reenviar, consultar más tarde, no reenviar |
| `fuente` | Manual Técnico v150, Nota Técnica N o guía oficial |
| `vigencia` | Desde y hasta cuándo aplica, por ambiente |

## Reglas de esta carpeta

- La clasificación sale de la documentación oficial. Lo que se conoce solo por experiencia de integración se
  marca como tal y se registra en [`contradicciones.md`](../contradicciones.md) si choca con lo documentado.
- Un código eliminado por una Nota Técnica no se borra: se le pone fecha de fin.
