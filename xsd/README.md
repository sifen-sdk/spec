# xsd

**Propósito.** Una copia fiel de los esquemas XSD oficiales de SIFEN, para que los SDK puedan validar la
estructura de un documento sin conexión a la red y de forma reproducible.

**Estado.** 47 esquemas en [`oficial/`](oficial), descargados el 26/11/2026 de `https://ekuatia.set.gov.py/sifen/xsd/` y verificados contra el origen. El índice está en [`indice.json`](indice.json).

## Titularidad

Los esquemas fueron publicados por la **Dirección Nacional de Ingresos Tributarios (DNIT)** y le pertenecen. Se
incluyen sin modificar su contenido, con el único fin de permitir la interoperabilidad con SIFEN, y **no quedan
cubiertos por la licencia Apache-2.0** de este proyecto. Ver [`NOTICE`](../NOTICE) y la
[ADR 0006](../docs/adr/0006-xsd-incluidos-con-procedencia.md).

## Qué se registra de cada archivo

En [`indice.json`](indice.json), por cada esquema:

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

## Archivos generados

- [`arbol.json`](arbol.json): volcado neutral de los esquemas (tipos, elementos, ocurrencias y restricciones), generado
  por `tools/xsd_arbol.py`. No se edita a mano; la integración continua verifica que esté al día.
- [`cobertura.json`](cobertura.json): qué esquemas deben tener todos sus elementos en [`campos/`](../campos/README.md)
  y qué elementos están exceptuados por una contradicción registrada.

El formato completo está en [`FORMATO.md`](../FORMATO.md).
