---
kind: gate-step
id: "gate-step:integrity.27"
title: "Model routing lint checks its own vacuity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:233"
extractor: "workflows"
tags: [protected]
aliases:
  - "Model routing lint checks its own vacuity"
  - "integrity.27"
generated: true
---

# Model routing lint checks its own vacuity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:233`

## Statement

python3 scripts/lint_model_routing.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_model_routing.py --self-test |
| `kind` | run |
| `ordinal` | 27 |

## Binds

- **runs** → [[module__scripts_lint_model_routing|MR001-MR005: model routing policy conformance, checked before any spawn.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
