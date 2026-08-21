---
kind: gate-step
id: "gate-step:database.06"
title: "CriterionRunner — materialization, execution, verdict composition"
shape: "step"
job: "database"
source: ".github/workflows/gates.yml:367"
extractor: "workflows"
tags: [protected]
aliases:
  - "CriterionRunner — materialization, execution, verdict composition"
  - "database.06"
generated: true
---

# CriterionRunner — materialization, execution, verdict composition

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:367`

## Statement

uv run pytest harness/criterion

## Fields

| Field | Value |
|---|---|
| `command` | uv run pytest harness/criterion |
| `kind` | run |
| `ordinal` | 6 |

## Binds

- **runs** → [[module__harness_criterion|harness.criterion]]
- [[gate__database|database (throwaway cluster, roles and grants)]] **contains** → this
