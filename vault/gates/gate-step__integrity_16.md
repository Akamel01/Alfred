---
kind: gate-step
id: "gate-step:integrity.16"
title: "Stage gate lint detects planted violations"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:150"
extractor: "workflows"
tags: [protected]
aliases:
  - "Stage gate lint detects planted violations"
  - "integrity.16"
generated: true
---

# Stage gate lint detects planted violations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:150`

## Statement

python3 scripts/lint_stage_gates.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_stage_gates.py --self-test |
| `kind` | run |
| `ordinal` | 16 |

## Binds

- **runs** → [[module__scripts_lint_stage_gates|The stage gate, as a check rather than as a sentence somebody reads.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
