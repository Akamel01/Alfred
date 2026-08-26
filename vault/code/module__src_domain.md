---
kind: module
id: "module:src.domain"
title: "src.domain"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/domain:1"
extractor: "code"
aliases:
  - "src.domain"
generated: true
---

# src.domain

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/domain:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | true |
| `tree` | src |

## Binds

- **contains** → [[module__src_domain_arrays|Array-valued fields for Pydantic boundary models.]]
- **contains** → [[module__src_domain_base|Base model and the invariants every persisted record carries.]]
- **contains** → [[module__src_domain_errors|Error taxonomy (docs/tier1/failure-semantics.md).]]
- **contains** → [[module__src_domain_trajectory|Trajectory schemas — the load-bearing abstraction everything downstream reads.]]
