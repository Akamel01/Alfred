---
kind: module
id: "module:src.api"
title: "src.api"
shape: "package"
present: "true"
protected: "false"
lint_gated: "true"
source: "src/api:1"
extractor: "code"
aliases:
  - "src.api"
generated: true
---

# src.api

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `src/api:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | src |

## Binds

- **contains** → [[module__src_api___init__|The deployable unit. Deliberately almost empty.]]
- **contains** → [[module__src_api_app|Health and identity. The identity is the load-bearing half.]]
