---
kind: gate-step
id: "gate-step:integrity.28"
title: "Model routing policy conforms to the bindings"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:236"
extractor: "workflows"
tags: [protected]
aliases:
  - "Model routing policy conforms to the bindings"
  - "integrity.28"
generated: true
---

# Model routing policy conforms to the bindings

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:236`

## Statement

python3 scripts/lint_model_routing.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_model_routing.py |
| `kind` | run |
| `ordinal` | 28 |

## Binds

- **runs** → [[module__scripts_lint_model_routing|MR001-MR005: model routing policy conformance, checked before any spawn.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
