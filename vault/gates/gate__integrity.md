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
- **contains** → [[gate-step__integrity_06|ADR numbers are claimed once]]
- **contains** → [[gate-step__integrity_07|ADR number lint detects planted collisions]]
- **contains** → [[gate-step__integrity_08|Migrations are additive-only]]
- **contains** → [[gate-step__integrity_09|Verdict boundary holds]]
- **contains** → [[gate-step__integrity_10|Verdict boundary lint detects planted violations]]
- **contains** → [[gate-step__integrity_11|CI coverage (test directories, failure register)]]
- **contains** → [[gate-step__integrity_12|CI coverage lint detects planted violations]]
- **contains** → [[gate-step__integrity_13|Harness lint coverage]]
- **contains** → [[gate-step__integrity_14|Harness gate detects planted violations]]
- **contains** → [[gate-step__integrity_15|Stage gate register integrity]]
- **contains** → [[gate-step__integrity_16|Stage gate lint detects planted violations]]
- **contains** → [[gate-step__integrity_17|ACS-1 vectors regenerate byte-identically]]
- **contains** → [[gate-step__integrity_18|Vault generator detects its own vacuity]]
- **contains** → [[gate-step__integrity_19|Vault and published graph are current]]
- **contains** → [[gate-step__integrity_20|Protected paths append-only (bench/results/, bench/fingerprints/)]]
- **contains** → [[gate-step__integrity_21|Topology lint checks its own vacuity]]
- **contains** → [[gate-step__integrity_22|Topology file is valid]]
- **contains** → [[gate-step__integrity_23|Orchestration canvas is current]]
- **contains** → [[gate-step__integrity_24|Vault generator suites]]
- [[gate__database|database (throwaway cluster, roles and grants)]] **needs** → this
- [[gate__inspector|inspector (ACS-1, lane, bench)]] **needs** → this
- [[gate__product|product (lint, types, tests)]] **needs** → this
