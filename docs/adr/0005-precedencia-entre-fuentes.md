# 0005 · Precedencia entre Manual, Notas Técnicas y XSD

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

La especificación efectiva de SIFEN es la suma de tres fuentes: el Manual Técnico v150, las Notas Técnicas y los
esquemas XSD publicados. No existe un manual consolidado, y las fuentes divergen: los esquemas tienen elementos
que el Manual no describe y les faltan otros que sí describe, y hay puntos en que una Nota Técnica y el esquema
dicen cosas opuestas. La DNIT además modifica los esquemas sin cambiarles el nombre ni la versión.

Sin un criterio escrito, cada SDK resolvería cada conflicto a su manera.

## Decisión

Ante un conflicto se aplica este orden:

1. **Estructura** (elementos, orden, tipos de dato): manda el **XSD** publicado.
2. **Reglas** (obligatoriedad, condiciones, fórmulas, plazos): manda la **Nota Técnica más reciente** que trate
   el punto.
3. **Lo demás**: el **Manual Técnico** es la base.
4. **Ante la duda, manda lo que SIFEN acepta**, verificado contra el ambiente de test.

Cada conflicto se registra en [`contradicciones.md`](../../contradicciones.md): qué dice cada fuente, qué se
decidió, cómo se verificó y en qué estado está.

Como el ambiente de test valida menos que producción, una aceptación en test se anota como **verificación
parcial**, no como caso cerrado.

## Consecuencias

- Los conflictos son visibles y la decisión es la misma en todos los SDK.
- Cada esquema se guarda con su hash, para detectar cuándo la DNIT lo cambió (ADR 0006).
- Algunas entradas quedarán abiertas hasta poder probarlas contra SIFEN.

## Alternativas descartadas

- **El Manual como única verdad:** está desactualizado respecto de las notas y de los esquemas.
- **El XSD como única verdad:** no expresa reglas condicionales, fórmulas ni plazos.
- **Resolver caso por caso en el código:** deja la decisión invisible y distinta en cada lenguaje.
