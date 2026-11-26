# 0007 · Cobertura de tipos de documento y eventos

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

El objetivo es cubrir todo lo que SIFEN documenta, pero no todo lo documentado está habilitado:

- Tipos **1** (factura), **4** (autofactura), **5** (nota de crédito), **6** (nota de débito) y **7** (nota de
  remisión): habilitados.
- Tipos **2** (factura de exportación), **3** (factura de importación) y **8** (comprobante de retención):
  figuran como "futuro" en el Manual Técnico y están comentados en los esquemas. La factura de exportación está
  en un piloto cuyo protocolo advierte posibles cambios de campos y validaciones.
- Tipos **9** y **10** (boletas): aparecen solo en el esquema, sin norma ni descripción en el Manual.

Con los eventos pasa algo parecido: unos se envían, otros solo se reciben al consultar, y otros no están
habilitados.

## Decisión

**Documentos**

- Tipos 1, 4, 5, 6 y 7: cobertura **completa**, incluidos los grupos por sector.
- Tipos 2, 3 y 8: se **modelan según el Manual** y se marcan **"no habilitado por SIFEN"**. El SDK avisa de ese
  estado; no promete que SIFEN los acepte.
- Tipos 9 y 10: **fuera** hasta que exista una norma que los defina.

**Eventos**

- Los ocho que se envían: cancelación, inutilización, nominación, actualización de datos de transporte, y los
  cuatro del receptor (notificación de recepción, conformidad, disconformidad y desconocimiento).
- Los que solo llegan en una consulta se **leen**, no se envían.
- Los no habilitados (por ejemplo, endoso) quedan **fuera** hasta que SIFEN los habilite.

La **contingencia** se modela como campo, no como flujo: SIFEN hoy la rechaza.

## Consecuencias

- "Todos los tipos" queda dicho con precisión: lo habilitado, completo; lo futuro, modelado y señalado.
- Lo marcado como no habilitado puede cambiar cuando SIFEN lo habilite; ese cambio no se considera una ruptura.
- El estado de habilitación es un dato de la especificación, con su fuente y su vigencia.

## Alternativas descartadas

- **Omitir los tipos futuros:** obliga a rehacer el modelo cuando se habiliten.
- **Tratarlos como habilitados:** promete algo que SIFEN rechaza.
- **Modelar los tipos 9 y 10 a partir del esquema:** sin norma, sería inventar reglas (ADR 0002).
