---
kind: gate-step
id: "gate-step:integrity.15"
title: "Harness lint coverage"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:146"
extractor: "workflows"
tags: [protected]
aliases:
  - "Harness lint coverage"
  - "integrity.15"
generated: true
---

# Harness lint coverage

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:146`

## Statement

python3 scripts/lint_harness_gate.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_harness_gate.py |
| `kind` | run |
| `ordinal` | 15 |

## Binds

- **runs** → [[module__scripts_lint_harness_gate|How much of `harness/` the lint gate actually collects, and whether it can go red.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
