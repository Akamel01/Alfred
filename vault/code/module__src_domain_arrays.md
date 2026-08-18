---
kind: module
id: "module:src.domain.arrays"
title: "Array-valued fields for Pydantic boundary models."
shape: "module"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/domain/arrays.py:1"
extractor: "code"
aliases:
  - "Array-valued fields for Pydantic boundary models."
  - "src.domain.arrays"
generated: true
---

# Array-valued fields for Pydantic boundary models.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/domain/arrays.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | src/domain/arrays.py |
| `tree` | src |

## Binds

- [[module__src_domain|src.domain]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0001|Representation of undefined and infinite metric values]] **enforced_by** → this — """Array-valued fields for Pydantic boundary models.

The domain is vectorized on purpose. ADR-0001 measured per-timeste
