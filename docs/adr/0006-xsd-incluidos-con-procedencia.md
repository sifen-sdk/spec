# 0006 · XSD de la DNIT incluidos con procedencia y hash

- **Estado:** Aceptada
- **Fecha:** 2026-11-26

## Contexto

Validar un documento contra el esquema oficial es la red de seguridad de la estructura. Los esquemas se publican
en el sitio de la DNIT con la leyenda "todos los derechos reservados" y sin licencia. No hay un paquete
descargable: los archivos se incluyen unos a otros por dirección absoluta, y la DNIT los modifica sin cambiarles
el nombre ni la versión.

## Decisión

Los esquemas se **incluyen en este repositorio**, en [`xsd/`](../../xsd/README.md), sin modificar su contenido.

Por cada archivo se registra la **procedencia** (dirección oficial), la **fecha de descarga** y el **hash
SHA-256**.

Se deja constancia de la **titularidad de la DNIT**: los esquemas no quedan cubiertos por la licencia Apache-2.0
del proyecto (ver [`NOTICE`](../../NOTICE)). Se incluyen solo para permitir la interoperabilidad con SIFEN.

En paralelo se **consulta a la DNIT** sobre la redistribución. Esa consulta está pendiente. Si la respuesta fuera
negativa, se pasa a descargar los esquemas al compilar, verificando el hash registrado.

## Consecuencias

- Los SDK validan sin conexión a la red y las compilaciones son reproducibles.
- El hash permite detectar cuándo la DNIT cambia un esquema; una revisión periódica compara el publicado con el
  registrado.
- El proyecto redistribuye material de un tercero sin licencia explícita: es un riesgo aceptado, acotado por el
  aviso de titularidad, la consulta a la DNIT y la alternativa ya prevista.

## Alternativas descartadas

- **Descargar al compilar:** la compilación depende de que el sitio de la DNIT esté disponible y sin cambios.
  Queda como alternativa si la DNIT objeta la inclusión.
- **Esperar la respuesta de la DNIT antes de incluir nada:** deja la validación de estructura sin fecha.
- **Reescribir los esquemas:** dejarían de ser la referencia oficial.
