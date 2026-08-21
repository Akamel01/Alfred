---
kind: gate-step
id: "gate-step:integrity.13"
title: "Stage gate register integrity"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:133"
extractor: "workflows"
tags: [protected]
aliases:
  - "Stage gate register integrity"
  - "integrity.13"
generated: true
---

# Stage gate register integrity

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:133`

## Statement

python3 scripts/lint_stage_gates.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_stage_gates.py |
| `kind` | run |
| `ordinal` | 13 |

## Binds

- **runs** → [[module__scripts_lint_stage_gates|The stage gate, as a check rather than as a sentence somebody reads.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
