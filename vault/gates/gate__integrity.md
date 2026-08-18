---
kind: gate
id: "gate:integrity"
title: "integrity (fixtures and register)"
shape: "job"
job: "integrity"
source: ".github/workflows/gates.yml:37"
extractor: "workflows"
tags: [protected]
aliases:
  - "integrity"
  - "integrity (fixtures and register)"
generated: true
---

# integrity (fixtures and register)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:37`

## Fields

| Field | Value |
|---|---|
| `ordinal` | 1 |

## Binds

- **contains** → [[gate-step__integrity_01|Install uv]]
- **contains** → [[gate-step__integrity_02|Set up Python]]
- **contains** → [[gate-step__integrity_03|Sync dependencies from the lockfile]]
- **contains** → [[gate-step__integrity_04|Document header contract]]
- **contains** → [[gate-step__integrity_05|Reading map current]]
- **contains** → [[gate-step__integrity_06|Migrations are additive-only]]
- **contains** → [[gate-step__integrity_07|Verdict boundary holds]]
- **contains** → [[gate-step__integrity_08|Verdict boundary lint detects planted violations]]
- **contains** → [[gate-step__integrity_09|ACS-1 vectors regenerate byte-identically]]
- [[gate__database|database (throwaway cluster, roles and grants)]] **needs** → this
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **needs** → this
- [[gate__product|product (lint, types, tests)]] **needs** → this
