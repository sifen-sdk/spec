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
### C-NNN · <título corto>

- **Fuentes en conflicto:** <Manual Técnico v150, campo o validación · Nota Técnica N · XSD, archivo y elemento · guía>
- **Qué dice cada una:**
  - <fuente 1>: <qué establece>
  - <fuente 2>: <qué establece>
- **Decisión:** <qué aplican la especificación y los SDK>
- **Cómo se verificó:** <lectura de documentos · prueba contra el ambiente de test (fecha) · pendiente>
- **Estado:** abierta | resuelta | resuelta con verificación parcial
```

## Entradas

Todavía no hay entradas. Se cargan en la fase 1, a medida que se releva cada grupo de campos y cada Nota Técnica.
