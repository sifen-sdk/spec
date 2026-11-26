# reglas

**Propósito.** Lo que SIFEN exige de cada campo, expresado como datos. Los SDK aplican estas reglas antes de
enviar; no tienen reglas propias.

**Estado.** Sin datos. Se carga en la fase 1.

## Principio

El SDK exige **exactamente** lo que SIFEN documenta:

- **Obligatorio** → se exige siempre.
- **Opcional** → no se exige nunca.
- **Condicional** → se exige solo cuando se cumple la condición documentada.
- **Prohibido** → si SIFEN indica que un campo no debe informarse en cierto caso, se rechaza.

No se agregan reglas que SIFEN no documenta ni se completan valores por defecto.

## Qué lleva cada regla

| Dato | Descripción |
|---|---|
| `id` | Identificador estable de la regla |
| `campo` | Campo de [`campos/`](../campos/README.md) al que aplica |
| `tipo` | `obligatorio`, `opcional`, `condicional`, `prohibido` o `aritmetica` |
| `condicion` | Para `condicional` y `prohibido`: cuándo aplica (ver abajo) |
| `fuente` | Campo o validación del Manual Técnico v150, Nota Técnica N, o XSD |
| `vigencia` | Fecha desde y hasta, **por ambiente** (test y producción) |
| `codigo_sifen` | Código de rechazo de SIFEN asociado, si está documentado |

Una regla sin `fuente` no se acepta.

## Condiciones

Las condiciones son declarativas, para que cualquier lenguaje las pueda evaluar sin un intérprete de expresiones:

- Comparaciones simples sobre campos: igual a, distinto de, está en una lista, está presente, está ausente.
- Combinadores: `todas` (se cumplen todas), `alguna` (se cumple al menos una), `no` (negación).

No hay funciones, aritmética ni código dentro de una condición.

## Verificaciones aritméticas

Son las fórmulas que SIFEN documenta entre campos (por ejemplo, la relación entre el total de un ítem, su base
gravada y su IVA). Cada una tiene un identificador y la fórmula tal como figura en la fuente. La implementación la
escribe cada SDK y queda fijada por los casos de [`conformidad/`](../conformidad/README.md).

**Una verificación aritmética nunca modifica un valor.** Compara lo que cargó el sistema emisor con lo que resulta
de la fórmula y, si no coinciden, informa el campo, la regla y la fuente. Solo se admiten las holguras que la
documentación de SIFEN escribe de forma explícita.

## Vigencia

Las reglas se activan por fecha y por ambiente, no por versión de formato: la versión del formato no cambia desde
2019, y las Notas Técnicas entran en fechas distintas en test y en producción. Una regla derogada no se borra: se
le pone fecha de fin.
