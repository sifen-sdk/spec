# E-002 — Documentos y eventos de la fase 4 en el ambiente de test (2026-11-27)

- **Ambiente:** test (`sifen-test.set.gov.py`): recepción síncrona (`siRecepDE`), eventos (`siRecepEvento`) y
  consulta de DE (`siConsDE`).
- **Fecha:** 2026-11-27.
- **Documentos y eventos:** Manual Técnico v150, firmados con el certificado de un emisor habilitado en test. El
  receptor de las facturas es el propio emisor, así que los eventos del receptor se firman con el mismo certificado.
- **Herramientas:** `LiveDocumentsTest` y `LiveEventsTest` del SDK Java (`sifen-sdk-java`).
- **Qué no incluye:** datos del emisor, credenciales ni XML enviados.

## Documentos

`APR` = aprobado (0260). `REC nnnn` = rechazado con ese código. Los mensajes llevan el prefijo "TEST - ".

| Documento | Resultado |
|---|---|
| Nota de débito (C002 = 6), motivo 6, asociada por CDC a una factura aprobada | APR |
| Autofactura (C002 = 4), vendedor no contribuyente con cédula paraguaya sintética | REC 2562 ("El vendedor no debe ser contribuyente"): la cédula figuraba en el registro de contribuyentes |
| Autofactura, vendedor con pasaporte sintético (E304 = 2), constancia de no contribuyente sin número (H002 = 3, H014 = 1) | APR |
| Autofactura con F008 + 1 | REC 2362 |
| Autofactura con EA008 de un ítem + 1 | REC 1853 |
| Nota de remisión (C002 = 7) con transporte terrestre completo, transportista incluido | APR |
| Nota de remisión sin transportista, un vehículo con E967 = 1 | REC 2300 |
| Nota de remisión sin transportista, dos vehículos (E967 = 1 y E967 = 2) | REC 2300 |
| Factura con transporte (entrega y un vehículo con matrícula, sin salida ni transportista) | APR |
| Factura con `gGrupEner` (consumo = lectura actual − anterior) | APR |
| Factura con `gGrupSeg` y una póliza | APR |
| Factura con `gGrupSup` | APR |
| Factura con `gGrupAdi` | APR |
| Factura a receptor innominado (D201 = 2, D208 = 5, `dNomRec` "Sin Nombre") | APR |

La autofactura válida no lleva F002 a F005 (prohibidos con C002 = 4) y su F008 es la suma de los EA008: SIFEN no
aplica R-F008-A1 a la autofactura (C-517).

## Eventos

| Evento | Resultado |
|---|---|
| Cualquier evento, con `gGroupGesEve` sin `xsi:schemaLocation` | REC 0160 ("XML mal formado") |
| El mismo evento firmado, con `xmlns:xsi` pero sin `xsi:schemaLocation` | REC 0160 |
| El mismo evento firmado, con `xsi:schemaLocation="http://ekuatia.set.gov.py/sifen/xsd siRecepEvento_v150.xsd"` | Registrado (0600) |
| Notificación de recepción, sobre una factura propia | 0600 |
| Conformidad total | 0600 |
| Disconformidad | 0600 |
| Desconocimiento | 0600 |
| Cancelación de una factura aprobada minutos antes | 0600 |
| Nominación de la factura innominada | 0600 |
| Inutilización de dos números de factura | 0600 |
| Actualización de datos del transporte (cambio de chofer) sobre la nota de remisión | 0600 |

La firma de los eventos es la misma que la del DE: enveloped sobre `rEve`, referenciada por su `Id`, con una sola
transformación (NT 16), `Signature` como hermano siguiente de `rEve` dentro de `rGesEve`.

## Consulta de un DE con eventos

La consulta de una factura con dos eventos registrados respondió 0422 con `xContenDE` como **texto escapado** que
contiene, sin raíz `rContDe`:

```
rDE (con su Signature y gCamFuFD)
dProtAut
xContEv
  rContEv                      (uno por evento)
    xEvento
      rGesEve  (rEve y Signature, tal como se envió)
    rResEnviEventoDe
      rRetEnviEventoDe
        dFecProc
        gResProcEVe (dEstRes, dProtAut, gResProc/dCodRes, dMsgRes)
```

Hay un solo `xContEv` con un `rContEv` por evento.

## Pendiente

- D017 = 1 con `dTiCamIt` informado (rechazo 1855 esperado, C-303) y F036 (C-504).
- Eventos registrados por la SET u otros (solo consulta): no se pueden provocar desde un emisor.
