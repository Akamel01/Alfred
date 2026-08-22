---
kind: gate-step
id: "gate-step:integrity.06"
title: "ADR numbers are claimed once"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:71"
extractor: "workflows"
tags: [protected]
aliases:
  - "ADR numbers are claimed once"
  - "integrity.06"
generated: true
---

# ADR numbers are claimed once

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:71`

## Statement

python3 scripts/lint_adr_numbers.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_adr_numbers.py |
| `kind` | run |
| `ordinal` | 6 |

## Binds

- **runs** → [[module__scripts_lint_adr_numbers|ADR number claim lint: a branch may not claim a number the base has issued.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
