---
kind: module
id: "module:src.provenance"
title: "src.provenance"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/provenance:1"
extractor: "code"
aliases:
  - "src.provenance"
generated: true
---

# src.provenance

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/provenance:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | src |

## Binds

- **contains** → [[module__src_provenance___init__|Result stamping and the one ACS-1 door (ADR-0003, ADR-0004).]]
- **contains** → [[module__src_provenance_encoding|The single door to ACS-1 (ADR-0003, ADR-0004).]]
- **contains** → [[module__src_provenance_stamp|Result stamping — metric version, code commit, assumption set, input hash, tolerance.]]
