---
kind: gate-step
id: "gate-step:integrity.06"
title: "Migrations are additive-only"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:70"
extractor: "workflows"
tags: [protected]
aliases:
  - "Migrations are additive-only"
  - "integrity.06"
generated: true
---

# Migrations are additive-only

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:70`

## Statement

python3 scripts/lint_migrations.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_migrations.py |
| `kind` | run |
| `ordinal` | 6 |

## Binds

- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
