# Seguridad

## Cómo reportar un problema

**No abras un issue público.** Usá el reporte privado de GitHub: pestaña **Security** de este repositorio →
**Report a vulnerability**. El reporte solo lo ven los mantenedores.

Incluí qué encontraste, cómo reproducirlo y qué impacto le ves.

En este repositorio, un problema de seguridad es, por ejemplo:

- un dato de la especificación que haría que un SDK acepte o firme un documento que no debería;
- material sensible subido por error (certificados, claves, códigos de seguridad, datos de personas o empresas).

Un error en una regla o en un catálogo que no tiene impacto de seguridad va como issue común.

## Nunca publiques material real

Ni en issues, ni en pull requests, ni en discusiones:

- certificados, claves privadas, contraseñas ni códigos de seguridad (CSC);
- RUC, timbrados, códigos de control (CDC) ni XML de producción sin anonimizar.

Si ya publicaste algo así, avisá por el reporte privado y **revocá o cambiá** esa credencial: borrar el mensaje no
alcanza, porque el contenido pudo haber sido copiado.

## Alcance

Las vulnerabilidades del código de un SDK se reportan en el repositorio de ese SDK, por ejemplo
[sifen-sdk-java](https://github.com/sifen-sdk/sifen-sdk-java/security).
