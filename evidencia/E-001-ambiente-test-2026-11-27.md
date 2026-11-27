# E-001 — Verificaciones aritméticas en el ambiente de test (2026-11-27)

- **Ambiente:** test (`sifen-test.set.gov.py`), servicio de recepción síncrona (`siRecepDE`).
- **Fecha:** 2026-11-27.
- **Documentos:** facturas electrónicas (C002 = 1) y notas de crédito (C002 = 5), Manual Técnico v150, firmadas con
  un certificado de un emisor habilitado en test. Receptor: el propio emisor.
- **Método:** para cada regla se envió primero un documento correcto y después variantes con **un solo** importe
  desplazado en una cantidad conocida (1 y 100 en guaraníes; 0,01 a 1,00 en dólares). El resto del documento se
  mantuvo coherente. Herramienta: `LiveArithmeticProbeTest` del SDK Java (`sifen-sdk-java`).
- **Qué no incluye:** datos del emisor, credenciales ni XML enviados.

## Resultado general

1. SIFEN verifica casi todas las fórmulas con código de rechazo, incluso con **1 guaraní** de diferencia.
2. Un valor se acepta si su diferencia con el resultado **exacto** de la fórmula es **≤ 0,5** en la unidad del campo.
   Si la regla documenta una holgura (0,8 en EA003 y EA004), la tolerancia es esa holgura, sin sumar el 0,5.
3. Los totales se comparan contra la **suma de los valores informados** en los ítems: calcular el IVA sobre los
   subtotales ("vertical") se rechaza cuando no coincide con esa suma.

## Detalle

`APR` = aprobado (0260). `REC nnnn` = rechazado con ese código. Los mensajes llevan el prefijo "TEST - ".

### Documentos correctos

| Caso | Resultado |
|---|---|
| Ítems al 10 % y al 5 %, exento y exonerado, IVA por ítem y totales como suma | APR |
| Descuento global por porcentaje (F010 = 10) | APR |
| Gravado parcial (E731 = 4, fórmula de la NT 13) | APR |
| USD, tipo de cambio global (D017 = 1), sin `dTiCamIt` en los ítems | APR |
| USD, tipo de cambio por ítem (D017 = 2) | APR |
| Redondeo a múltiplo de 50 (F013) | APR |

### Cálculo sobre los subtotales

| Caso | Resultado |
|---|---|
| IVA y bases totales calculados sobre F004/F005, ítems por ítem | REC 2377 |
| Solo el IVA total por tasa calculado sobre F004/F005 | REC 2367 |
| Base de un ítem con el otro redondeo (exacto 9094,545, informado 9094) y totales como suma | REC 1911 |
| IVA de un ítem en 909 cuando el exacto es 909,5 (diferencia 0,5) | APR |

### Un importe desplazado (guaraníes)

Con +1 y con +100 el resultado fue el mismo:

| Campo | Regla | Resultado |
|---|---|---|
| E727 total bruto por ítem | R-E727-A1 | REC 1859 |
| EA003 % de descuento | R-EA003-A1 | REC 1861 (+1); +100 no pasa el XSD |
| EA004 descuento global por ítem | R-EA004-A1/A2 | REC 1862 |
| EA008 total por ítem | R-EA008-A1 | REC 1853 |
| E735 base gravada 10 % / 5 % | R-E735-A3/A5 · A2/A4 | REC 1911 / 1910 |
| E735 base gravada de un ítem exento | R-E735-A1 | REC 1909 |
| E736 IVA por ítem | R-E736-A2 | REC 1913 |
| E736 IVA de un ítem exento | R-E736-A1 | REC 1912 |
| E737 base exenta (gravado / parcial) | R-E737-A2 / A1 | REC 1921 |
| F002 subtotal exento (también con parcial) | R-F002-A2 | REC 2353 |
| F003 subtotal exonerado | R-F003-A1 | REC 2355 |
| F004 subtotal 5 % | R-F004-A2 | REC 2357 |
| F005 subtotal 10 % (también con parcial) | R-F005-A2 | REC 2359 |
| F008 total bruto | R-F008-A1 | REC 2362 |
| F009 total descuento por ítem | R-F009-A2 | REC 2363 |
| F011 total descuentos | R-F011-A2 | REC 2364 |
| F012 total anticipos | R-F012-A2 | REC 2388 |
| F014 total general | R-F014-A3 | REC 2365 |
| F015 IVA 5 % | R-F015-A1 | REC 2367 |
| F016 IVA 10 % | R-F016-A1 | REC 2369 |
| F017 IVA total | R-F017-A1 | REC 2371 |
| F018 base 5 % | R-F018-A1 | REC 2373 |
| F019 base 10 % | R-F019-A1 | REC 2375 |
| F020 base total | R-F020-A1 | REC 2377 |
| F033 total descuento global | R-F033-A2 | REC 2383 |
| F034 total anticipo por ítem | R-F034-A2 | REC 2384 |
| F035 total anticipo global | R-F035-A2 | REC 2387 |
| F023 total en guaraníes, cambio global (+1 y +100 Gs.) | R-F023-A1 | REC 2385 |
| EA009 total por ítem en guaraníes, cambio por ítem | R-EA009-A1 | REC 1858 |
| F023 total en guaraníes, cambio por ítem | R-F023-A2 | REC 2386 |

### Tolerancia

| Caso | Resultado |
|---|---|
| USD, F016 + 0,01 / 0,02 / 0,05 / 0,10 / 0,49 / 0,50 | APR |
| USD, F016 + 0,51 / 0,99 / 1,00 | REC 2369 |
| USD, base de un ítem + 0,01 (diferencia con el exacto ≈ 0,012) | APR |
| USD, base de un ítem + 0,50 (diferencia con el exacto ≈ 0,502) | REC 1911 |
| EA003 + 0,01 / 0,49 / 0,50 / 0,51 / 0,80 (holgura 0,8) | APR |
| EA003 + 0,81 | REC 1861 |
| EA004 en USD + 0,50 / 0,80 (holgura 0,8) | APR |
| EA004 en USD + 0,81 / 1,00 | REC 1862 |
| EA004 en guaraníes + 1 | REC 1862 |

### Redondeo, comisión y F017

| Caso | Resultado |
|---|---|
| F013 = 1 y F013 = 100, con un total general que no queda en múltiplo de 50 | APR: SIFEN no verifica R-F013-A1 |
| Redondeo 49, sin F037, F017 = F015 + F016 | APR |
| Redondeo 49, F037 = 4, F017 = F016 − 4 (tabla) | APR |
| Redondeo 49, F037 = 4, F017 = F016 (validación 2371) | REC 2371 |
| Redondeo 49, F037 = 5 y F037 = 24, F017 restando ese valor | APR: SIFEN no verifica F037 |
| Comisión 1000, F026 = 100, F017 = F015 + F016 + 100 (tabla) | APR |
| Comisión 1000, F026 = 100, F017 = F015 + F016 (validación 2371) | REC 2371 |
| Comisión 1000, F026 = 101, F017 sumando 101 | APR: SIFEN no verifica F026 |

### Notas de crédito (H004)

| Caso | Resultado |
|---|---|
| Factura de 11000; NC de 5500 | APR |
| Segunda NC de 5500 (suma igual a la factura) | APR |
| Tercera NC de 5500 (suma mayor que la factura) | REC 2417 |
| Otra factura de 11000; NC de 11001 | REC 2417 |

## Otras observaciones

- La consulta de RUC (`siConsRUC`) respondió dos veces seguidas con `rRetEnviDe` código 0160 ("XML Mal Formado")
  y después respondió normalmente (0502) al mismo pedido. No se identificó la causa.
- Se reporta solo el primer error: SIFEN devolvió un único código por documento aunque hubiera más de un importe
  afectado.

## Pendiente

- Autofactura (R-EA008-A2, R-F008-A3), eventos (R-GEI006, R-GEN004, R-GED004) y consumo del sector energía
  (R-E797): el SDK todavía no genera esos documentos.
- F036 (IVA del redondeo al 5 %) y D017 = 1 con `dTiCamIt` informado (rechazo 1855 esperado, C-303).
- Producción: estas pruebas no se pueden hacer allí sin emitir documentos reales.
