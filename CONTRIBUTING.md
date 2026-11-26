# Cómo contribuir a spec

Gracias por ayudar. Este repositorio es la especificación de SIFEN como datos, así que las reglas para contribuir
son pocas y estrictas. Para lo general (conducta, flujo de trabajo, revisión) aplica el
[CONTRIBUTING de sifen-sdk-java](https://github.com/sifen-sdk/sifen-sdk-java/blob/main/CONTRIBUTING.md).

## 1. Todo cita su fuente oficial

Un campo, una regla, un código de catálogo o un código de respuesta nuevo debe indicar de dónde sale:

- el campo o la validación del **Manual Técnico v150**,
- la **Nota Técnica** (número y fecha), o
- el **XSD** (archivo y elemento).

Un cambio sin fuente no se acepta. "Así lo hace tal librería" o "a mí me funcionó" no es una fuente: si lo que
SIFEN acepta difiere de lo documentado, se registra en [`contradicciones.md`](contradicciones.md) con la forma en
que se verificó.

## 2. Nunca datos reales

No subas, ni en archivos ni en issues ni en pull requests:

- RUC, nombres, direcciones, teléfonos o emails de personas o empresas reales;
- certificados, claves privadas, contraseñas ni códigos de seguridad (CSC);
- números de timbrado ni códigos de control (CDC) reales;
- XML de producción sin anonimizar por completo.

Los casos de prueba usan solo datos sintéticos.

## 3. Sin reglas inventadas

La especificación exige exactamente lo que SIFEN documenta. No se agregan validaciones "por las dudas" ni valores
por defecto. Ver las [decisiones](docs/adr/README.md).

## 4. Commits

- Mensajes con [Conventional Commits](https://www.conventionalcommits.org/es/), por ejemplo
  `feat(reglas): receptor innominado según Nota Técnica 24`.
- Firmá cada commit con el DCO: `git commit -s`. Con esa firma declarás que tenés derecho a aportar el cambio
  bajo la licencia del proyecto ([Developer Certificate of Origin](https://developercertificate.org/)).

## 5. Decisiones

Un cambio de criterio (precedencia entre fuentes, formato de los datos, alcance) va con una ADR en
[`docs/adr/`](docs/adr/README.md), a partir de la [plantilla](docs/adr/0000-plantilla.md).
