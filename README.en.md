# SIFEN SDK · spec

> Community project. **Not affiliated with DNIT** (Paraguay's tax authority) and not endorsed by it.
> [Español](README.md) (source of truth)

The specification of SIFEN, Paraguay's national electronic invoicing system, **as data**, independent of any
programming language. It is the single source consumed by every SDK in the
[`sifen-sdk`](https://github.com/sifen-sdk) organization, starting with
[`sifen-sdk-java`](https://github.com/sifen-sdk/sifen-sdk-java).

## Status

**Phase 0: structure and decisions.** No data yet. Fields, rules, code tables, schemas and conformance cases are
added in phase 1.

## Principles

1. **Transport and verify, never compute.** Amounts are computed by the issuing system. The spec describes the
   formulas SIFEN documents so an SDK can *check* the values it receives, never change them.
2. **Require exactly what SIFEN documents.** Mandatory, optional, conditional or forbidden: nothing more, nothing
   less. No invented rules or default values.
3. **Every item cites its source.** Technical Manual field or validation, Technical Note, or XSD, with its
   effective dates.
4. **Effective by date and by environment.** Technical Notes take effect on different dates in test and production.
5. **Contradictions are recorded.** See [`contradicciones.md`](contradicciones.md).

## Layout

| Folder | Content |
|---|---|
| `campos/` | Field table for documents and events |
| `reglas/` | Requiredness and dependency rules, and arithmetic checks |
| `catalogos/` | Code tables with effective dates |
| `respuestas/` | Classified SIFEN response codes |
| `xsd/` | Copy of the official schemas with provenance, date and hash |
| `conformidad/` | Conformance cases every SDK must pass |
| `contradicciones.md` | Conflicts between the Manual, Technical Notes and XSD, and the decision taken |
| `docs/adr/` | Decision records |

Folder names and documentation are in Spanish, the language of the official specification.

## License

Original content is licensed under [Apache-2.0](LICENSE). The XSD schemas and tables published by DNIT belong to
DNIT and are not covered by that license: see [`NOTICE`](NOTICE).
