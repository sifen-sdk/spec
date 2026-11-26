# conformidad

**Propósito.** La batería de casos que todo SDK de la organización debe pasar. Es lo que garantiza que el SDK de
Java y los de otros lenguajes se comporten igual.

**Estado.** Sin casos. Se cargan desde la fase 1.

## Tipos de caso previstos

| Tipo | Entrada | Resultado esperado |
|---|---|---|
| Generación | Un documento o evento en formato neutral | El XML sin firmar, el código de control (CDC) y el hash del QR |
| Validación | Un documento con un defecto conocido | Los errores esperados: campo, regla y fuente |
| Aritmética | Un documento con importes coherentes o incoherentes | Qué verificaciones pasan y cuáles fallan |
| Vigencia | El mismo documento con dos fechas o dos ambientes | Resultados distintos según la regla vigente |
| Respuestas | Una respuesta de SIFEN de ejemplo | El resultado interpretado: clase, código y mensaje |

## Reglas de esta carpeta

- **Solo datos sintéticos.** Ningún RUC, nombre, timbrado, CDC, certificado ni código de seguridad real. Un XML
  tomado de un caso real se anonimiza por completo antes de entrar.
- Cada regla de [`reglas/`](../reglas/README.md) tiene al menos un caso que la cumple y uno que la viola.
- Cada Nota Técnica tiene al menos un caso.
- Los casos no incluyen la firma digital esperada: depende del certificado. Lo que se fija es el contenido que se
  firma y cómo se verifica.
- Un caso no se modifica para que un SDK pase. Si el caso está mal, se corrige citando la fuente.
