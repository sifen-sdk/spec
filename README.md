# SIFEN SDK · spec

> Proyecto comunitario. **No está afiliado a la DNIT** ni cuenta con su respaldo.
> [English](README.en.md)

La especificación de SIFEN (Sistema Integrado de Facturación Electrónica Nacional, Paraguay) **como datos**,
neutral al lenguaje de programación. Es la fuente única que consumen todos los SDK de la organización
[`sifen-sdk`](https://github.com/sifen-sdk), empezando por
[`sifen-sdk-java`](https://github.com/sifen-sdk/sifen-sdk-java).

## Estado

**Completa y en uso por el SDK de Java.** Manual Técnico v150, Notas Técnicas 1 a 27 y los esquemas publicados
el 19/09/2025.

| Contenido | Cantidad |
|---|---|
| Campos (documento electrónico, eventos, web services) | 715 |
| Reglas (obligatoriedad, condiciones, formato, fórmulas) | 1.249 |
| Catálogos | 62 |
| Códigos de respuesta | 510 |
| Contradicciones registradas | 137 |
| Esquemas oficiales | 47 |

Lo verificado contra el ambiente de test de SIFEN está en [`evidencia/`](evidencia): el comportamiento de cada fórmula
de importes (E-001), cada tipo de documento y evento (E-002), y el IVA del redondeo, el tipo de cambio por ítem y la
conexión TLS (E-003). De las 137 contradicciones, 16 ya están verificadas por completo o en parte.

```bash
python3 tools/validar.py --cobertura   # formato, fuentes, referencias y cobertura de los esquemas
python3 tools/conformidad.py           # casos de conformidad calculables (CDC y QR)
```

El formato de los datos está en [`FORMATO.md`](FORMATO.md).

## Por qué existe

La especificación real de SIFEN está repartida en tres fuentes que no siempre coinciden: el Manual Técnico v150,
las Notas Técnicas y los esquemas XSD publicados. Cada librería existente la reinterpretó por su cuenta, a mano y
sin dejar constancia de dónde sale cada regla.

Este repositorio la reúne una sola vez, en un formato que cualquier lenguaje puede leer, con la fuente de cada
dato. Así todos los SDK se comportan igual y una Nota Técnica nueva es un cambio de datos, no una reescritura en
cada lenguaje.

## Principios

1. **Transportar y verificar, no calcular.** Los importes los calcula el sistema emisor. La especificación describe
   las fórmulas que SIFEN documenta para que el SDK pueda *comprobar* los valores recibidos, nunca modificarlos.
2. **Exigir exactamente lo que SIFEN documenta.** Obligatorio, opcional, condicional o prohibido: ni más ni menos.
   No hay reglas ni valores por defecto inventados.
3. **Cada dato cita su fuente.** Campo o validación del Manual Técnico, Nota Técnica o XSD, con su vigencia.
4. **Vigencia por fecha y por ambiente.** Las Notas Técnicas entran en fechas distintas en test y en producción.
5. **Las contradicciones se registran, no se esconden.** Ver [`contradicciones.md`](contradicciones.md).

Las decisiones completas están en [`docs/adr/`](docs/adr/README.md).

## Estructura

| Carpeta | Contenido |
|---|---|
| [`campos/`](campos/README.md) | Tabla de campos de los documentos y eventos: identificador, nombre XML, grupo, tipo, longitud, ocurrencia, fuente y vigencia |
| [`reglas/`](reglas/README.md) | Reglas de obligatoriedad y dependencia (declarativas) y verificaciones aritméticas |
| [`catalogos/`](catalogos/README.md) | Tablas de códigos (países, monedas, geografía, unidades de medida, etc.) con su vigencia |
| [`respuestas/`](respuestas/README.md) | Códigos de respuesta de SIFEN, clasificados |
| [`xsd/`](xsd/README.md) | Copia de los esquemas oficiales con procedencia, fecha y hash |
| [`conformidad/`](conformidad/README.md) | Casos de prueba que todo SDK debe pasar |
| [`contradicciones.md`](contradicciones.md) | Conflictos entre Manual, Notas Técnicas y XSD, y qué se decidió en cada uno |
| [`evidencia/`](evidencia/) | Resultados de pruebas contra SIFEN que deciden cómo se comporta en la práctica |
| [`docs/adr/`](docs/adr/README.md) | Registro de decisiones |

## Cómo contribuir

Leé [`CONTRIBUTING.md`](CONTRIBUTING.md). Lo esencial: todo campo o regla nuevo cita su fuente oficial, y nunca
se suben datos reales.

Para reportar un problema de seguridad, ver [`SECURITY.md`](SECURITY.md).

## Licencia

El contenido propio se distribuye bajo [Apache-2.0](LICENSE). Los esquemas XSD y las tablas publicadas por la DNIT
pertenecen a la DNIT y no quedan cubiertos por esa licencia: ver [`NOTICE`](NOTICE).
