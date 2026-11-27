# Contradicciones entre las fuentes de SIFEN

## Propósito

La especificación de SIFEN está repartida en el Manual Técnico v150, las Notas Técnicas y los esquemas XSD
publicados. En varios puntos esas fuentes no coinciden entre sí, o no coinciden con lo que SIFEN acepta en la
práctica.

Este archivo registra cada conflicto y la decisión que tomó el proyecto, para que la decisión sea visible,
discutible y la misma en todos los SDK.

## Criterio de precedencia

1. **Estructura** (qué elementos existen, en qué orden, de qué tipo): manda el **XSD** publicado.
2. **Reglas** (obligatoriedad, condiciones, fórmulas, plazos): manda la **Nota Técnica más reciente** que trate
   el punto.
3. **Todo lo demás**: el **Manual Técnico** es la base.
4. **Ante la duda, manda lo que SIFEN acepta**, verificado contra el ambiente de test. El ambiente de test puede
   validar menos que producción, así que una aceptación en test no cierra el caso por sí sola: se anota como
   verificación parcial.

Detalle y fundamento en la [ADR 0005](docs/adr/0005-precedencia-entre-fuentes.md).

## Plantilla de entrada

```markdown
## C-NNN — <título corto>

- **Fuentes en conflicto:** <Manual Técnico v150, campo o validación · Nota Técnica N · XSD, archivo y elemento · guía>
- **Qué dice cada una:**
  - <fuente 1>: <qué establece>
  - <fuente 2>: <qué establece>
- **Decisión:** <qué aplican la especificación y los SDK>
- **Cómo se verificó:** <lectura de documentos · prueba contra el ambiente de test (fecha) · pendiente>
- **Estado:** pendiente de verificación. | resuelta. | resuelta con verificación parcial.
```

## Entradas

Las entradas viven en [`contradicciones.d/`](contradicciones.d), un archivo por área, para que varias personas
puedan cargar a la vez sin pisarse. Los ids son únicos en todo el repositorio y el validador lo comprueba.

| Archivo | Área | Entradas |
|---|---|---|
| [00.md](contradicciones.d/00.md) | Transversales | 1 |
| [01.md](contradicciones.d/01.md) | Documento: grupos A a D | 11 |
| [02.md](contradicciones.d/02.md) | Documento: grupos E a E7 | 8 |
| [03.md](contradicciones.d/03.md) | Documento: ítems (E8) | 12 |
| [04.md](contradicciones.d/04.md) | Documento: sectores y transporte (E9, E10) | 9 |
| [05.md](contradicciones.d/05.md) | Documento: totales, generales, asociado, firma y QR (F a J) | 17 |
| [06.md](contradicciones.d/06.md) | Eventos | 19 |
| [07.md](contradicciones.d/07.md) | Web services | 24 |
| [08.md](contradicciones.d/08.md) | Códigos de respuesta | 17 |
| [09.md](contradicciones.d/09.md) | Catálogos | 19 |

De las 137 entradas, 12 están **resueltas**, 6 **resueltas con verificación parcial** y 119 **pendientes de
verificación** (tienen una decisión tomada leyendo los documentos, pero SIFEN todavía no la confirmó). Las entradas se
verifican contra el ambiente de test a medida que se acumula evidencia en [`evidencia/`](evidencia/); cada una dice si
se puede probar desde un contribuyente en test, si solo se observa en producción o si un emisor no la puede provocar.
