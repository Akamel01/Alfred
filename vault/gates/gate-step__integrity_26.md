---
kind: gate-step
id: "gate-step:integrity.26"
title: "Ownership router homes exist and no gate cites runtime state"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:230"
extractor: "workflows"
tags: [protected]
aliases:
  - "Ownership router homes exist and no gate cites runtime state"
  - "integrity.26"
generated: true
---

# Ownership router homes exist and no gate cites runtime state

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:230`

## Statement

python3 scripts/lint_state_authority.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_state_authority.py |
| `kind` | run |
| `ordinal` | 26 |

## Binds

- **runs** → [[module__scripts_lint_state_authority|SA001-SA003: the ownership router's mechanical half, checked.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
