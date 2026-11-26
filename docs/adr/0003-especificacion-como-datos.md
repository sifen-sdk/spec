# 0003 · Especificación como datos y batería de conformidad compartida

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

El proyecto es un SDK, no una librería de un solo lenguaje: Java es la primera implementación y habrá otras. Si
cada lenguaje reinterpreta el Manual Técnico y las Notas Técnicas por su cuenta, los SDK van a divergir, y cada
Nota Técnica nueva habrá que implementarla una vez por lenguaje.

## Decisión

La especificación vive en este repositorio **como datos neutrales al lenguaje**: tabla de campos, reglas de
obligatoriedad y dependencia, catálogos, códigos de respuesta y esquemas.

- Las **reglas de obligatoriedad y dependencia** son declarativas: comparaciones simples sobre campos combinadas
  con `todas`, `alguna` y `no`. Cualquier lenguaje las evalúa sin un intérprete de expresiones.
- Las **verificaciones aritméticas** se registran con un identificador y la fórmula tal como figura en la fuente.
  Cada SDK las implementa en su lenguaje.
- Una **batería de conformidad** compartida fija el comportamiento: mismas entradas, mismos resultados. Un SDK es
  conforme si pasa todos los casos.
- Los **nombres legibles** de los campos son los mismos en todos los lenguajes.

## Consecuencias

- Todos los SDK se comportan igual, y eso se puede comprobar.
- Una Nota Técnica es, en la mayoría de los casos, un cambio de datos acá más un release de cada SDK.
- Dos líneas mayores de un mismo SDK pueden consumir la misma especificación.
- Este repositorio tiene su propio ciclo de versiones, y cada SDK declara qué versión de la especificación usa.
- Hay que mantener un validador de la propia especificación (formato, fuentes, coherencia con los XSD).

## Alternativas descartadas

- **Especificación dentro del repositorio de Java:** ata la especificación al ciclo y a las formas de un lenguaje.
- **Un lenguaje de expresiones general para todas las reglas, incluidas las fórmulas:** obliga a escribir y
  mantener un intérprete en cada lenguaje.
- **Generar todo el código de cada SDK desde los datos:** descartado para el modelo de Java, que se escribe a mano
  y se comprueba contra la tabla de campos con una prueba.
