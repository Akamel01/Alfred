---
kind: gate
id: "gate:mutation"
title: "mutation control (the suite's own negative control)"
shape: "job"
job: "mutation"
source: ".github/workflows/gates.yml:407"
extractor: "workflows"
tags: [protected]
aliases:
  - "mutation"
  - "mutation control (the suite's own negative control)"
generated: true
---

# mutation control (the suite's own negative control)

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `.github/workflows/gates.yml:407`

## Fields

| Field | Value |
|---|---|
| `ordinal` | 5 |

## Binds

- **contains** → [[gate-step__mutation_01|Install uv]]
- **contains** → [[gate-step__mutation_02|Set up Python]]
- **contains** → [[gate-step__mutation_03|Sync dependencies from the lockfile]]
- **contains** → [[gate-step__mutation_04|ACS-1 mutation control]]
- **needs** → [[gate__inspector|inspector (ACS-1, lane, bench)]]
