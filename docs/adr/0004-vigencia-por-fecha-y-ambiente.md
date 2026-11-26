# 0004 · Reglas activadas por fecha y por ambiente

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

La versión del formato de SIFEN es la 150 desde 2019. Los cambios posteriores llegaron como Notas Técnicas (27 a
marzo de 2026) que modifican campos, reglas, fórmulas y plazos sin cambiar esa versión.

Cada Nota Técnica entra en vigencia en fechas distintas en el ambiente de test y en producción, y el preaviso no
es confiable: hubo notas con diez días de anticipación y alguna con ninguno. Además, hay reglas cuyo valor cambia
con el tiempo, como el monto a partir del cual no se admite un receptor innominado.

## Decisión

Cada campo, regla, código de catálogo y código de respuesta lleva su **vigencia: fecha desde y hasta, por
ambiente** (test y producción).

Al validar, el SDK aplica lo vigente para la **fecha del documento** y el **ambiente** de destino. La fecha sale
del documento, no del reloj de la máquina.

Lo derogado **no se borra**: se le pone fecha de fin. Así se puede validar o leer un documento anterior con las
reglas de su momento.

No hay interruptores para activar o desactivar una Nota Técnica.

## Consecuencias

- Una Nota Técnica nueva se carga con sus fechas en cuanto se publica, y empieza a aplicar sola.
- El mismo documento puede dar resultados distintos en test y en producción, o antes y después de una fecha. Eso
  es correcto y se cubre con casos de conformidad.
- Cargar una regla exige conocer sus fechas. Cuando la nota no las declara, se anota la fecha del documento y se
  marca como no declarada.

## Alternativas descartadas

- **Activar por versión de formato:** la versión no cambia, así que no distingue nada.
- **Interruptores por Nota Técnica, apagados por defecto:** dejan al integrador con reglas viejas sin saberlo.
- **Aplicar siempre la regla más nueva:** rompe la validación de documentos anteriores y la diferencia entre
  ambientes.
