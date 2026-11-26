# xsd

**Propósito.** Una copia fiel de los esquemas XSD oficiales de SIFEN, para que los SDK puedan validar la
estructura de un documento sin conexión a la red y de forma reproducible.

**Estado.** Sin archivos. Se cargan en la fase 1.

## Titularidad

Los esquemas fueron publicados por la **Dirección Nacional de Ingresos Tributarios (DNIT)** y le pertenecen. Se
incluyen sin modificar su contenido, con el único fin de permitir la interoperabilidad con SIFEN, y **no quedan
cubiertos por la licencia Apache-2.0** de este proyecto. Ver [`NOTICE`](../NOTICE) y la
[ADR 0006](../docs/adr/0006-xsd-incluidos-con-procedencia.md).

## Qué se registra de cada archivo

En un índice dentro de esta carpeta, por cada esquema:

| Dato | Descripción |
|---|---|
| `archivo` | Nombre del archivo |
| `origen` | URL oficial de la que se descargó |
| `descargado` | Fecha de descarga |
| `modificado` | Fecha de última modificación que informa el servidor de origen |
| `sha256` | Hash SHA-256 del archivo tal como se descargó |

## Reglas de esta carpeta

- Los archivos no se editan ni se reformatean. Si para usarlos sin red hace falta resolver referencias entre
  esquemas, eso se hace con un catálogo de resolución aparte, no tocando los archivos.
- La DNIT modifica los esquemas sin cambiarles el nombre ni la versión. Por eso el hash es lo que identifica una
  copia: cuando el esquema publicado cambia, se agrega la copia nueva con su fecha y se revisan campos y reglas.
- Si un esquema y el Manual Técnico no coinciden, se registra en [`contradicciones.md`](../contradicciones.md).
