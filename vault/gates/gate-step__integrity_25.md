---
kind: gate-step
id: "gate-step:integrity.25"
title: "State authority lint checks its own vacuity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:227"
extractor: "workflows"
tags: [protected]
aliases:
  - "State authority lint checks its own vacuity"
  - "integrity.25"
generated: true
---

# State authority lint checks its own vacuity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:227`

## Statement

python3 scripts/lint_state_authority.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_state_authority.py --self-test |
| `kind` | run |
| `ordinal` | 25 |

## Binds

- **runs** → [[module__scripts_lint_state_authority|SA001-SA003: the ownership router's mechanical half, checked.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
