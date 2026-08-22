---
kind: gate-step
id: "gate-step:integrity.07"
title: "ADR number lint detects planted collisions"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:76"
extractor: "workflows"
tags: [protected]
aliases:
  - "ADR number lint detects planted collisions"
  - "integrity.07"
generated: true
---

# ADR number lint detects planted collisions

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:76`

## Statement

python3 scripts/lint_adr_numbers.py --self-test

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_adr_numbers.py --self-test |
| `kind` | run |
| `ordinal` | 7 |

## Binds

- **runs** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
