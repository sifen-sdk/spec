# conformidad

**Propósito.** La batería de casos que todo SDK de la organización debe pasar. Es lo que garantiza que el SDK de
Java y los de otros lenguajes se comporten igual.

**Estado.** Beta. Hay casos de CDC y QR (los ejemplos oficiales del Manual Técnico), de validación, de aritmética, de
vigencia y de respuestas. Toda regla aritmética vigente y no descartada tiene un caso que la cumple y uno que la
viola, salvo las seis que no se pueden verificar con un documento solo (ver [`cobertura.json`](cobertura.json)).

```bash
python3 tools/generar_conformidad.py   # regenera los casos de validación, aritmética, vigencia y respuestas
python3 tools/conformidad.py           # verifica formato, coherencia con las reglas, cobertura y que estén al día
python3 tools/conformidad.py --xsd     # además valida cada XML contra el XSD oficial (necesita lxml)
```

## Carpetas

| Carpeta | Contenido | Quién la escribe |
|---|---|---|
| `cdc/`, `qr/` | Ejemplos del Manual Técnico: entrada y resultado esperado en el JSON | A mano |
| `bases/` | Documentos y eventos válidos, sin firmar: la entrada del generador | Una sola vez (ver abajo) |
| `validacion/` | Cada base, válida; y bases a las que se les quitó un campo que una regla exige | `tools/generar_conformidad.py` |
| `aritmetica/` | Una base con un solo importe alterado: viola una regla aritmética | `tools/generar_conformidad.py` |
| `vigencia/` | La misma factura evaluada en dos fechas o dos ambientes, con resultados distintos | `tools/generar_conformidad.py` |
| `respuestas/` | Respuestas de SIFEN y cómo se interpretan | `tools/generar_conformidad.py` |
| `cobertura.json` | Las reglas aritméticas que no tienen caso, con el motivo | A mano |

Los casos generados no se editan a mano: se cambia el generador, las bases o las reglas y se regenera.
`tools/conformidad.py` falla si un caso no está al día.

## Formato de un caso

Un JSON por caso y su XML **al lado**, con el mismo nombre. El XML va en un archivo aparte y no dentro del JSON
porque así se lee y se compara sin escapes, se valida con cualquier herramienta de XSD y un SDK lo carga tal cual,
sin pasar por su lector de JSON.

### Validación, aritmética y vigencia

La entrada es un XML **sin firmar** en el "formato neutral" de la especificación: el `rDE` de un documento electrónico
(sin `Signature` ni `gCamFuFD`, que agrega el firmante) o el `rGesEve` de un evento (sin `Signature`), en el espacio de
nombres de SIFEN.

```json
{
  "tipo": "aritmetica",
  "descripcion": "El total bruto del ítem es el precio unitario por la cantidad. Falla: se suma una unidad al valor informado (E727)",
  "base": "factura",
  "xml": "factura-r-e727-a1.xml",
  "regla": "R-E727-A1",
  "cambio": { "campo": "E727", "ruta": "rDE/DE/gDtipDE/gCamItem[1]/gValorItem/dTotBruOpeItem", "antes": "121000", "despues": "121001" },
  "evaluaciones": [
    {
      "ambiente": "test",
      "fecha": "2026-11-20",
      "esperado": {
        "xsd": true,
        "fallan": [{ "regla": "R-E727-A1", "campo": "E727" }],
        "pasan": ["R-E735-A4", "R-F008-A1"],
        "otras": "prohibidas"
      }
    }
  ]
}
```

| Dato | Descripción |
|---|---|
| `tipo` | `validacion`, `aritmetica` o `vigencia`; coincide con la carpeta |
| `descripcion` | Qué se prueba, en una frase |
| `base` | El documento de `bases/` del que sale el caso |
| `xml` | El XML del caso, en la misma carpeta. En vigencia puede faltar si cada evaluación indica el suyo |
| `regla` | Solo aritmética y faltas de presencia: la regla que el caso viola a propósito |
| `cambio` / `quitados` | Solo informativo: el valor que se alteró (campo, ruta, antes, después) o los campos que se quitaron |
| `evaluaciones` | Una en validación y aritmética; dos o más en vigencia, con resultados distintos |

Cada evaluación:

| Dato | Descripción |
|---|---|
| `ambiente` | `test` o `produccion` |
| `fecha` | `AAAA-MM-DD`. La fecha que elige las reglas vigentes: la de emisión del DE (D002) o la de firma del evento (GDE004). Es siempre la del XML |
| `xml` | Solo en vigencia: el XML de esta evaluación, cuando el documento cambia de fecha |
| `esperado.xsd` | Si el XML valida contra el XSD oficial (el `DE` contra `DE_v150.xsd`, el `rEve` contra `Evento_v150.xsd`) |
| `esperado.fallan` | Las reglas que el SDK debe informar, cada una con el campo (`campo` de la regla) en que la informa |
| `esperado.pasan` | Reglas que aplican al documento y se cumplen: el SDK **no** debe informarlas |
| `esperado.otras` | `prohibidas`: el SDK no debe informar ningún otro error. `permitidas`: el caso solo fija `fallan` y `pasan` |

Un SDK pasa el caso cuando, en ese ambiente y en esa fecha: el resultado del XSD es el esperado, informa cada regla de
`fallan` en su campo, no informa ninguna de `pasan` y, si `otras` es `prohibidas`, no informa ningún otro error. Una
regla de `fallan` que el SDK no puede verificar (por ejemplo, porque no la implementa) cuenta como no informada. Las
advertencias no cuentan como errores.

### Respuestas

La entrada es la respuesta de SIFEN tal como llega: el sobre SOAP 1.2 completo.

```json
{
  "tipo": "respuestas",
  "descripcion": "Recepción de dos eventos: uno aprobado y otro rechazado",
  "xml": "evento-mixto.xml",
  "entrada": { "servicio": "evento" },
  "esperado": {
    "resultados": [
      { "id": "1", "estado": "aprobado", "protocolo": "1234567893", "mensajes": [{ "codigo": "0600", "clase": "aprobacion" }] },
      { "id": "2", "estado": "rechazado", "protocolo": null, "mensajes": [{ "codigo": "4003", "clase": "rechazo" }] }
    ]
  }
}
```

| Dato | Descripción |
|---|---|
| `entrada.servicio` | `recepcion` (respuesta `rRetEnviDe` de `siRecepDE`) o `evento` (`rRetEnviEventoDe` de `siRecepEvento`) |
| `entrada.cdc` | Solo recepción: el CDC del documento enviado |
| `esperado.resultados` | Uno por documento o evento, en orden: `id` (CDC o id del evento), `estado` (`aprobado`, `aprobado_con_observacion`, `rechazado`), `protocolo` (`dProtAut`, o `null`) y `mensajes` en orden |
| `mensajes[].clase` | La clase del código en [`respuestas/`](../respuestas/README.md); la verifica `tools/conformidad.py` |

## Cómo se generan

1. **Bases.** Documentos válidos con datos sintéticos: factura con ítems al 10 %, al 5 %, exento, exonerado y gravado
   parcial; factura en dólares con tipo de cambio global y por ítem; factura del sector energía; autofactura; notas
   de crédito, débito y remisión; y los ocho eventos (cancelación, inutilización, nominación, actualización de
   transporte, notificación de recepción, conformidad, disconformidad y desconocimiento). Se produjeron una sola vez
   con el modelo del SDK de Java y se validaron contra el XSD oficial (`tools/conformidad.py --xsd`). Desde entonces
   son datos: no dependen de ningún SDK.
2. **Resultado esperado.** Sale de las reglas, no de un SDK. `tools/generar_conformidad.py` trae una implementación de
   referencia mínima de la gramática de condiciones y de cada fórmula aritmética, con la igualdad de FORMATO.md
   (diferencia con el resultado exacto ≤ `holgura`, o ≤ 0,5 sin holgura). En las fórmulas, un importe opcional que no
   figura en el documento (descuentos, anticipos, subtotales, redondeo, comisión, IVA del redondeo y de la comisión)
   cuenta como 0; si falta un operando obligatorio, la regla no se verifica en ese documento.
3. **Casos aritméticos.** Por cada regla aritmética vigente en la fecha de las bases, no descartada y con verificación
   posible: la primera base donde la regla aplica y se cumple, con **un solo** valor alterado. Por defecto se suma una
   unidad al campo de la regla (más que el 0,5 de tolerancia y que la holgura de 0,8); las reglas de rango y de fechas
   de los eventos usan el cambio que las viola (rango de 1001 números, fin igual al inicio, recepción un día antes
   de la emisión). `fallan` son **todas** las reglas que el cambio viola según la referencia, no solo la buscada
   (por ejemplo, alterar F016 viola R-F016-A1 y R-F017-A1).
4. **Faltas de presencia.** Una lista corta en el generador: un campo que una regla `obligatorio` o `condicional`
   exige (con la condición cumplida en la base) y que el XSD permite omitir.
5. **Vigencia.** La factura base, con un ítem gravado parcial, en la transición de la Nota Técnica 13 (fórmulas de
   E735, E737, F002, F004 y F005): el mismo día en los dos ambientes y el día anterior y el de entrada en vigor en
   cada uno. El CDC se recalcula porque incluye la fecha. Estos casos permiten otras observaciones: en 2023 rigen
   otros catálogos y campos.
6. **Respuestas.** Respuestas sintéticas con la estructura del XSD de cada servicio y códigos de
   [`respuestas/`](../respuestas/README.md).

## Reglas de esta carpeta

- **Solo datos sintéticos.** Ningún RUC, nombre, timbrado, CDC, certificado ni código de seguridad real. Los RUC son
  los del ejemplo del Manual (44444401-7 y 44444402-5), los nombres dicen "de prueba" y los CDC se calculan con
  esos datos. Un XML tomado de un caso real se anonimiza por completo antes de entrar.
- Cada regla aritmética vigente de [`reglas/`](../reglas/README.md) tiene al menos un caso que la cumple y uno que la
  viola, salvo las registradas en `cobertura.json` con su motivo. `tools/conformidad.py` lo verifica.
- Cada Nota Técnica tiene al menos un caso.
- Los casos no incluyen la firma digital esperada: depende del certificado. Lo que se fija es el contenido que se
  firma y cómo se verifica.
- Un caso no se modifica para que un SDK pase. Si el caso está mal, se corrige citando la fuente.
