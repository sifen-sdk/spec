# 0002 · Exigir exactamente lo que SIFEN documenta

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

El valor de un SDK de integración está en que el integrador no tenga que releer el Manual Técnico para saber qué
campos cargar. Las librerías actuales reimplementan cientos de reglas a mano, sin indicar de dónde sale cada una:
algunas exigen cosas que SIFEN no pide, otras dejan pasar lo que SIFEN rechaza, y otras completan valores
ficticios para que el documento "pase".

## Decisión

El SDK exige cada campo **tal cual lo documenta SIFEN**, ni más ni menos:

- **Obligatorio** → se exige siempre.
- **Opcional** → no se exige nunca.
- **Condicional** → se exige solo bajo la condición documentada.
- **Prohibido** → si SIFEN indica que no debe informarse en cierto caso, se rechaza.

Cada regla **cita su fuente** (campo o validación del Manual Técnico, Nota Técnica, XSD) y su vigencia. Una regla
sin fuente no entra a la especificación.

El SDK **no inventa** reglas, ni valores por defecto, ni textos de relleno. Lo que el integrador no cargó, no
viaja.

## Consecuencias

- Cada error de validación indica el campo, la regla y dónde está documentada.
- Un cambio de SIFEN se refleja cambiando o fechando una regla, no reescribiendo código.
- Cargar la especificación completa con sus fuentes es el trabajo más largo del proyecto.
- Si SIFEN acepta en la práctica algo distinto de lo documentado, se resuelve con el registro de contradicciones
  (ADR 0005), no con una excepción silenciosa.

## Alternativas descartadas

- **Reglas a mano en el código de cada SDK:** sin trazabilidad y distintas en cada lenguaje.
- **Validar solo contra el XSD:** el XSD no expresa la obligatoriedad condicional ni las fórmulas.
- **Completar valores por defecto para evitar rechazos:** pone en un documento legal datos que el emisor no cargó.
