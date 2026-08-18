---
kind: gate-step
id: "gate-step:integrity.05"
title: "Reading map current"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:62"
extractor: "workflows"
tags: [protected]
aliases:
  - "Reading map current"
  - "integrity.05"
generated: true
---

# Reading map current

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:62`

## Statement

python3 scripts/gen_reading_map.py --check

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/gen_reading_map.py --check |
| `kind` | run |
| `ordinal` | 5 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
