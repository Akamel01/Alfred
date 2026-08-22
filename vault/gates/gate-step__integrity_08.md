---
kind: gate-step
id: "gate-step:integrity.08"
title: "Migrations are additive-only"
shape: "step"
job: "integrity"
source: ".github/workflows/gates.yml:84"
extractor: "workflows"
tags: [protected]
aliases:
  - "Migrations are additive-only"
  - "integrity.08"
generated: true
---

# Migrations are additive-only

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:84`

## Statement

python3 scripts/lint_migrations.py

## Fields

| Field | Value |
|---|---|
| `command` | python3 scripts/lint_migrations.py |
| `kind` | run |
| `ordinal` | 8 |

## Binds

- **runs** → [[module__scripts_lint_migrations|Additive-only lint over the evidence and held-out migration directories.]]
- [[gate__integrity|integrity (fixtures and register)]] **contains** → this
