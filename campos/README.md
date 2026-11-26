# campos

**Propósito.** La tabla de todos los campos de los documentos electrónicos y de los eventos de SIFEN. Es la base
del modelo de cada SDK: un SDK cubre un campo si y solo si figura acá.

**Estado.** Sin datos. Se carga en la fase 1.

## Formato previsto

Un archivo por grupo del XML (por ejemplo, datos del timbrado, emisor, receptor, ítems, totales) y uno por evento.
Cada campo lleva:

| Dato | Descripción |
|---|---|
| `id` | Identificador del campo en el Manual Técnico (por ejemplo, `F014`) |
| `xml` | Nombre del elemento en el XML (por ejemplo, `dTotOpe`) |
| `nombre` | Nombre legible en inglés que usan los SDK (por ejemplo, `operationTotal`) |
| `grupo` | Grupo del XML al que pertenece |
| `tipo` | Tipo de dato (texto, numérico, fecha, fecha y hora, código de catálogo) |
| `longitud` | Longitud mínima y máxima; para numéricos, enteros y decimales admitidos |
| `ocurrencia` | Mínimo y máximo de repeticiones |
| `catalogo` | Catálogo de [`catalogos/`](../catalogos/README.md) al que pertenece el valor, si corresponde |
| `fuente` | Dónde está definido: Manual Técnico v150, Nota Técnica N, XSD |
| `vigencia` | Desde y hasta cuándo aplica, por ambiente (test y producción) |

La obligatoriedad no va acá: va en [`reglas/`](../reglas/README.md), porque casi siempre depende de otros campos.

## Reglas de esta carpeta

- Todo campo cita su fuente oficial.
- Todo elemento de los esquemas de [`xsd/`](../xsd/README.md) figura en esta tabla, y todo campo de esta tabla
  existe en los esquemas. Las excepciones se registran en [`contradicciones.md`](../contradicciones.md).
- Los nombres legibles son los mismos en todos los lenguajes.
