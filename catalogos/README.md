# catalogos

**Propósito.** Las tablas de códigos que SIFEN usa en los documentos y eventos: tipos de documento, tipos de
transacción, afectación tributaria, condiciones y medios de pago, monedas, países, departamentos, distritos y
ciudades, unidades de medida, y el resto de las tablas del Manual Técnico y de las Notas Técnicas.

**Estado.** Sin datos. Se carga en la fase 1.

## Formato previsto

Un archivo por catálogo. Cada entrada lleva:

| Dato | Descripción |
|---|---|
| `codigo` | El código que viaja en el XML |
| `descripcion` | La descripción oficial, tal como SIFEN la exige en el campo de descripción asociado |
| `padre` | Para catálogos jerárquicos (departamento → distrito → ciudad), el código del nivel superior |
| `vigencia` | Desde y hasta cuándo es válido, por ambiente |

Cada archivo declara además su `fuente` (tabla del Manual Técnico, Nota Técnica o planilla oficial) y la fecha en
que se tomó.

## Reglas de esta carpeta

- Las descripciones se copian tal cual de la fuente oficial: SIFEN rechaza si la descripción no coincide con el
  código.
- Un código dado de baja no se borra: se le pone fecha de fin, porque los documentos anteriores lo siguen usando.
- Las tablas publicadas por la DNIT le pertenecen; ver [`NOTICE`](../NOTICE).
