# Formato de los datos

Todos los datos son archivos JSON en UTF-8. Los valida `tools/validar.py`, que es la referencia: si este documento y
el validador no coinciden, el error está acá.

```bash
python3 tools/validar.py               # valida todo lo cargado
python3 tools/validar.py --cobertura   # además: todo elemento de los esquemas cubiertos tiene su campo
python3 tools/xsd_arbol.py             # regenera xsd/arbol.json a partir de xsd/oficial
```

## Fuentes

Toda entrada (campo, regla, catálogo, respuesta) lleva `fuentes`: una lista no vacía de `{ "doc", "ref" }`.

| `doc` | Documento | `ref` esperado |
|---|---|---|
| `MT150` | Manual Técnico versión 150 | Id de campo (`E721`), número de validación (`1859`), o sección/tabla |
| `NT001` … `NT027` | Nota Técnica N | Campo, validación o apartado que modifica |
| `XSD` | Esquemas de `xsd/oficial` | Archivo y tipo o elemento |
| `GUIA-MP` | Guía de mejores prácticas para la gestión del envío de DE | Apartado |
| `GUIA-PRUEBAS` | Guía de pruebas | Apartado |
| `DEC872` | Decreto 872/2023 | Artículo |
| `RGnn-aaaa` | Resolución General nn/aaaa | Artículo |

Opcionalmente `pagina` (número) y `cita` (frase breve, literal).

## Vigencia

`vigencia` es opcional. Si falta, la entrada rige desde el Manual Técnico v150 en ambos ambientes.

```json
{ "desde": { "test": "2023-03-20", "produccion": "2023-06-17" }, "hasta": { "produccion": "2025-04-28" } }
```

Fechas `AAAA-MM-DD`. `null` significa que la fuente no publica la fecha para ese ambiente. Nada se borra: lo que
deja de regir recibe un `hasta`.

## `campos/*.json`

```json
{
  "grupo": "E8.1",
  "titulo": "Precio, tipo de cambio y valor total de la operación por ítem",
  "esquemas": ["DE_v150.xsd"],
  "campos": [
    {
      "id": "E727",
      "xml": "dTotBruOpeItem",
      "nombre": "grossTotal",
      "padre": "E720",
      "tipo": "numerico",
      "longitud": "1-15p(0-8)",
      "ocurrencia": "1-1",
      "descripcion": "Total bruto de la operación por ítem",
      "fuentes": [{ "doc": "MT150", "ref": "E727" }]
    }
  ]
}
```

| Dato | Obligatorio | Descripción |
|---|---|---|
| `id` | sí | Id del campo en el Manual Técnico. Único en toda la especificación |
| `xml` | sí | Nombre del elemento en el XML. Debe existir en alguno de los `esquemas` del archivo |
| `nombre` | sí | Nombre legible en inglés, `lowerCamelCase`, único bajo un mismo `padre`. Ver convenciones abajo |
| `padre` | sí (salvo la raíz) | `id` del grupo que lo contiene; `null` solo para la raíz |
| `tipo` | sí | `grupo`, `alfanumerico`, `numerico`, `fecha`, `fecha_hora`, `binario` o `xml` |
| `longitud` | no en grupos | Tal como la escribe el Manual (`1-15p(0-8)`, `3`, `1-255`) |
| `ocurrencia` | sí | Mínimo-máximo del Manual: `0-1`, `1-1`, `1-999`, `0-N` |
| `descripcion` | sí | Descripción oficial, breve |
| `observaciones` | no | Lo que el Manual anota y no es una regla (aclaraciones) |
| `catalogo` | no | `id` de un catálogo de `catalogos/` |
| `estado` | no | `vigente` (por defecto), `futuro` (documentado pero no habilitado) o `eliminado` |
| `contradiccion` | no | Id (`C-001`) de una entrada de `contradicciones.md` cuando las fuentes no coinciden |
| `fuentes`, `vigencia` | sí / no | Ver arriba |

La obligatoriedad real **no** se deduce de `ocurrencia`: está en `reglas/`.

### Convenciones para `nombre`

- Inglés, `lowerCamelCase`, sin el prefijo de tipo del XML (`d`, `i`, `c`, `g`) y sin abreviaturas del Manual.
- Dentro de un grupo no se repite el nombre del grupo: en el grupo de ítems, `description`, no `itemDescription`.
- Códigos: terminan en `Code` (`currencyCode`). Sus descripciones asociadas: `…Description`.
- Fechas: `…Date`; fecha y hora: `…DateTime`. Importes: `…Amount` o `…Total`. Porcentajes y tasas: `…Rate`.
- Grupos: sustantivo (`issuer`, `receiver`, `items`, `totals`).
- Términos fijos: RUC → `ruc`, dígito verificador → `checkDigit`, timbrado → `stamp`, establecimiento →
  `establishment`, punto de expedición → `dispatchPoint`, IVA → `vat`, ISC → `exciseTax`, CDC → `cdc`.

## `reglas/*.json`

```json
{
  "grupo": "E8.1",
  "reglas": [
    {
      "id": "R-E727-A1",
      "campo": "E727",
      "tipo": "aritmetica",
      "texto": "El total bruto del ítem es el precio unitario por la cantidad",
      "formula": "E727 = E721 * E711",
      "operandos": ["E721", "E711"],
      "codigo_sifen": "1859",
      "fuentes": [{ "doc": "MT150", "ref": "1859" }]
    }
  ]
}
```

| Dato | Obligatorio | Descripción |
|---|---|---|
| `id` | sí | `R-<campo>-<sufijo>`. Estable: no se reutiliza |
| `campo` | sí | `id` del campo al que aplica |
| `tipo` | sí | Ver tabla siguiente |
| `texto` | sí | Qué exige SIFEN, en una frase |
| `condicion` | según tipo | Cuándo aplica la regla |
| `no_declarativa` | no | `true` si la condición no se puede expresar con la gramática; entonces `texto` la describe completa |
| `formula`, `operandos` | en aritméticas | Fórmula tal como figura en la fuente, y los campos que intervienen |
| `holgura` | no | Tolerancia, solo si la fuente la escribe (ver "Igualdad en las reglas aritméticas") |
| `codigo_sifen` | no | Código de rechazo asociado |
| `contradiccion` | no | Id de `contradicciones.md` |
| `descartada` | no | `{ "contradiccion": "C-nnn", "evidencia": "E-nnn" }`: la regla queda registrada porque la fuente la escribe, pero SIFEN no la aplica (lo demuestra la evidencia). Los SDK no la verifican |
| `fuentes`, `vigencia` | sí / no | Ver arriba |

| `tipo` | Significado |
|---|---|
| `obligatorio` | El campo debe informarse siempre que exista su grupo padre |
| `opcional` | El campo puede omitirse siempre |
| `condicional` | El campo debe informarse cuando se cumple `condicion` |
| `prohibido` | El campo no debe informarse cuando se cumple `condicion` |
| `formato` | Restricción sobre el valor (largo, patrón, rango, catálogo) que no surge del XSD |
| `dependencia` | El valor depende de otro campo (por ejemplo, la descripción que corresponde a un código) |
| `aritmetica` | Relación numérica entre campos. Se verifica; nunca se corrige el valor |

### Condiciones

```json
{ "todas": [
    { "campo": "C002", "op": "en", "valores": ["1", "4"] },
    { "no": { "campo": "D202", "op": "presente" } }
] }
```

- Comparación con un valor: `igual`, `distinto`, `mayor`, `mayor_igual`, `menor`, `menor_igual` → `campo`, `op`, `valor`.
- Pertenencia: `en`, `no_en` → `campo`, `op`, `valores`.
- Presencia: `presente`, `ausente` → `campo`, `op`.
- Combinadores: `todas` y `alguna` (lista de dos o más), `no` (una condición).

Los valores se escriben como texto, igual que viajan en el XML. `mayor`, `mayor_igual`, `menor` y `menor_igual`
comparan como números decimales. `igual`, `distinto`, `en` y `no_en` consideran iguales dos valores con el mismo
texto **o** que son el mismo número decimal (`10.00` y `10`): el emisor transporta sus importes y tasas con su
propia escala, y comparar solo texto haría que una regla se saltee sin aviso. No hay funciones ni aritmética.

**Campos que se repiten** (por ejemplo, los de cada ítem):

- Si la regla y el campo de la condición están dentro del mismo grupo repetido, la condición se evalúa sobre la
  misma repetición (el mismo ítem).
- Si no, la condición se cumple cuando **alguna** repetición la cumple. Para exigir que la cumplan **todas**, se
  agrega `"cuantificador": "todos"` a la condición (`"alguno"` es el valor por defecto y puede escribirse).

Un campo ausente no cumple ninguna comparación de valor; solo cumple `ausente` y `no_en`.

### Igualdad en las reglas aritméticas

Un valor informado cumple una regla aritmética si su diferencia con el resultado **exacto** de la fórmula (sin
redondear, calculado con los valores informados) es:

- como máximo la `holgura` de la regla, cuando la tiene (por ejemplo, 0,8 en los porcentajes de descuento);
- como máximo **0,5** en la unidad del campo (guaraníes, dólares, puntos porcentuales…), cuando no la tiene.

Es lo que hace SIFEN, verificado en el ambiente de test ([E-001](evidencia/E-001-ambiente-test-2026-11-27.md)): con
0,50 aprueba y con 0,51 rechaza, en guaraníes y en dólares; con holgura 0,8 aprueba 0,80 y rechaza 0,81, sin sumar el
0,5. Las sumatorias usan los valores informados de cada ítem, nunca valores recalculados.

## `catalogos/<id>.json`

```json
{
  "id": "tipo-documento",
  "titulo": "Tipo de documento electrónico",
  "fuentes": [{ "doc": "MT150", "ref": "C002" }],
  "tomado": "2026-11-26",
  "entradas": [{ "codigo": "1", "descripcion": "Factura electrónica" }]
}
```

El `id` coincide con el nombre del archivo. A nivel de archivo, además:

| Dato | Descripción |
|---|---|
| `campos` | Ids de los campos que toman su valor de este catálogo |
| `descripciones` | Campo del código → campo de su descripción (`{"C002": "C003"}`) |
| `xml` | Elementos del XML que usan el catálogo |
| `nota`, `contradiccion` | Aclaraciones y contradicciones que afectan a todo el catálogo |
| `nombre` | Nombre en inglés del catálogo, en `snake_case` (`emission_type`). Los SDK lo usan para el tipo con constantes (un `enum` en Java) y lo convierten a su convención. Si está, cada entrada lleva el suyo |

Cada entrada lleva `codigo` y `descripcion` y, si corresponde:

| Dato | Descripción |
|---|---|
| `nombre` | Nombre en inglés de la constante, en `snake_case` y único en el catálogo (`contingency`). Obligatorio si el catálogo declara `nombre`. No viaja en el XML. Los catálogos grandes o geográficos (ciudad, distrito, país, moneda) no lo llevan |
| `padre` | Código del nivel superior en catálogos jerárquicos (departamento → distrito → ciudad) |
| `descripcion_xsd` | La descripción tal como la exige el XSD, cuando difiere de la del Manual. **Al emitir se usa esta** (el XSD manda en estructura y SIFEN rechaza otro texto) |
| `otras_descripciones` | Variantes que aparecen en otras fuentes, solo informativas |
| `descripcion_libre` | `true` si el código admite una descripción escrita por el emisor (por ejemplo, "Otro") |
| `significado`, `detalle`, `observacion` | Aclaraciones de la fuente que no viajan en el XML |
| `estado`, `vigencia`, `fuentes`, `contradiccion` | Como en el resto de la especificación |

## `respuestas/*.json`

```json
{ "respuestas": [
  { "codigo": "0260", "servicio": "recepcion", "mensaje": "Autorización del DE satisfactoria",
    "clase": "aprobacion", "accion": "ninguna", "fuentes": [{ "doc": "MT150", "ref": "0260" }] }
] }
```

`clase`: `aprobacion`, `aprobacion_con_observacion`, `rechazo`, `en_proceso`, `transitorio`, `bloqueo` o
`informativo`. La combinación `codigo` + `servicio` es única.

| Dato | Descripción |
|---|---|
| `servicio` | `recepcion`, `lote`, `consulta-lote`, `consulta-de`, `consulta-ruc`, `evento`, `consulta-masiva-ruc`, `generico`, `certificado`, `formato-de` o `formato-evento` |
| `efecto` | Tal como lo marca el Manual: `R` (rechazo), `A` o `AO` (aprobado con observación), `N` (notificación) |
| `accion` | `ninguna`, `corregir-y-reenviar`, `consultar-mas-tarde` o `no-reenviar`, solo si se deduce de la fuente |
| `campo`, `id_validacion` | Campo y validación del Manual a los que se refiere (por ejemplo `D208` y `D208c`) |
| `validacion` | Qué se comprueba, literal y breve |
| `historial` | Textos o efectos anteriores, cada uno con su `hasta` y su fuente |
| `duplicados` | Otras validaciones que el Manual numeró con el mismo código |

## `xsd/`

- `oficial/`: los esquemas, sin modificar. `indice.json`: origen, fecha y `sha256` de cada uno.
- `arbol.json`: volcado generado por `tools/xsd_arbol.py`. No se edita a mano.
- `cobertura.json`: `esquemas` cuyos elementos deben tener campo, y `excepciones` (`elemento` → id de
  contradicción) para los que no lo tienen.

## Ids que no da el Manual

Un elemento que existe solo en el XSD no tiene id oficial. Se le asigna `X-<grupo>-<elemento xml>` (por ejemplo
`X-H-dNumCuoDocAso`), se lo cita con fuente `XSD` y una contradicción, y se anota en `observaciones` que el id no es
oficial.

## Evidencia

`evidencia/E-nnn-<tema>.md`: resultados de pruebas contra SIFEN que deciden cómo se comporta en la práctica. Cada
archivo dice qué se envió, cuándo, a qué ambiente y qué respondió SIFEN (códigos y mensajes), sin datos del emisor ni
credenciales. Se citan desde `descartada` en las reglas y desde el estado de las contradicciones.

## `conformidad/`

Los casos de conformidad tienen su propio formato, descrito en [`conformidad/README.md`](conformidad/README.md): un
JSON por caso y su XML al lado. Los verifica `tools/conformidad.py` (no `tools/validar.py`), y los de validación,
aritmética, vigencia y respuestas los genera `tools/generar_conformidad.py`.

```bash
python3 tools/generar_conformidad.py   # regenera los casos a partir de conformidad/bases y de reglas/
python3 tools/conformidad.py           # formato, coherencia con las reglas, cobertura y que estén al día
python3 tools/conformidad.py --xsd     # además valida los XML contra el XSD oficial (necesita lxml)
```

## Contradicciones

El criterio y la plantilla están en [`contradicciones.md`](contradicciones.md). Las entradas viven en
`contradicciones.d/`, un archivo por área, cada una con un título `## C-nnn — …`; los ids son únicos en todo el
repositorio. Se citan desde `contradiccion` (un id o una lista) en campos, reglas, catálogos y respuestas.
