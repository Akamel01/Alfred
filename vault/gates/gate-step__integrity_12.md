---
kind: gate-step
id: "gate-step:integrity.12"
title: "Harness gate detects planted violations"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:124"
extractor: "workflows"
tags: [protected]
aliases:
  - "Harness gate detects planted violations"
  - "integrity.12"
generated: true
---

# Harness gate detects planted violations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:124`

## Statement

python3 scripts/lint_harness_gate.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_harness_gate.py --self-test |
| `kind` | run |
| `ordinal` | 12 |

## Binds

- **runs** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
