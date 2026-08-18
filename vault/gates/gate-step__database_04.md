---
kind: gate-step
id: "gate-step:database.04"
title: "Throwaway cluster, roles, grants and migrations"
shape: "step"
job: "database"
source: ".github/workflows/gates.yml:227"
extractor: "workflows"
tags: [protected]
aliases:
  - "Throwaway cluster, roles, grants and migrations"
  - "database.04"
generated: true
---

# Throwaway cluster, roles, grants and migrations

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:227`

## Statement

uv run pytest harness/db

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/db |
| `kind` | run |
| `ordinal` | 4 |

## Binds

- [[gate__database|database (throwaway cluster, roles and grants)]] **contains** → this
