# 0001 · El SDK transporta y verifica, no calcula

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

Los sistemas de facturación ya calculan sus importes: totales por ítem, descuentos, bases, IVA y redondeos. Las
librerías de SIFEN más usadas vuelven a calcular todo al generar el XML y descartan lo que cargó el sistema emisor,
sin forma de evitarlo. Cuando el criterio de la librería difiere del criterio del sistema (por ejemplo, redondear
el IVA por línea o por documento), el documento legal queda con importes distintos a los registrados, o SIFEN lo
rechaza.

A la vez, SIFEN sí recalcula los importes con las fórmulas del Manual Técnico y de las Notas Técnicas, y rechaza
el documento si no coinciden. El ambiente de test valida menos que producción, así que no alcanza con probar ahí.

## Decisión

El SDK **transporta** los importes tal como los recibe: nunca los modifica, completa ni redondea.

Antes de enviar, **verifica** que cumplan las fórmulas que SIFEN documenta. Si no las cumplen, falla indicando el
campo, la regla y la fuente. Solo se admiten las holguras que la documentación escribe de forma explícita.

El cálculo existe únicamente como **módulo opcional y separado**, que el integrador invoca de forma explícita y
cuyo resultado decide si usa. El núcleo nunca lo invoca.

El SDK sí deriva lo que es estructural y no una decisión del emisor: código de control, dígitos verificadores,
firma, QR y descripciones de catálogo.

## Consecuencias

- El XML dice lo mismo que el sistema emisor: no hay dos verdades sobre un importe.
- Los errores de coherencia aparecen en el sistema emisor, antes de enviar, con una explicación accionable.
- El integrador es responsable de calcular bien; el SDK le da la verificación y, si quiere, el cálculo de
  referencia.
- La especificación debe describir cada fórmula con su fuente y su vigencia.

## Alternativas descartadas

- **Calcular siempre dentro del SDK:** es el origen de los errores de redondeo de las librerías actuales.
- **Transportar sin verificar:** traslada los rechazos a producción, donde son difíciles de diagnosticar.
- **Calcular solo lo que falta:** vuelve impredecible qué valor termina en el documento.
