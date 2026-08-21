---
kind: gate
id: "gate:database"
title: "database (throwaway cluster, roles and grants)"
shape: "job"
job: "database"
source: ".github/workflows/gates.yml:309"
extractor: "workflows"
tags: [protected]
aliases:
  - "database"
  - "database (throwaway cluster, roles and grants)"
generated: true
---

# database (throwaway cluster, roles and grants)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:309`

## Fields

| Field | Value |
|---|---|
| `ordinal` | 4 |

## Binds

- **contains** → [[gate-step__database_01|Install uv]]
- **contains** → [[gate-step__database_02|Set up Python]]
- **contains** → [[gate-step__database_03|Sync dependencies from the lockfile]]
- **contains** → [[gate-step__database_04|Throwaway cluster, roles, grants and migrations]]
- **contains** → [[gate-step__database_05|EvidenceStore, chain re-walk, and the D-synthetic restore drill]]
- **contains** → [[gate-step__database_06|CriterionRunner — materialization, execution, verdict composition]]
- **needs** → [[gate__integrity|integrity (fixtures and register)]]
