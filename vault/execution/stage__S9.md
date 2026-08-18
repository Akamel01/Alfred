---
kind: stage
id: "stage:S9"
title: "Phase 1 build"
status: "not-started"
shape: "heading"
number: "S9"
source: "docs/tier2/execution-order.md:194"
extractor: "stages"
aliases:
  - "Phase 1 build"
  - "S9"
generated: true
---

# Phase 1 build

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:194`

## Statement

Phase 1 build · *blocked by S1–S8 and by O1*

## Fields

| Field | Value |
|---|---|
| `clause` | blocked by S1–S8 and by O1 |

## Stated in prose — unverified

- [[operator-item__O1|`F` (fixed weekly obligations, min/week) and target `n` (tasks/day, **stated as dispatched]] **blocks** → this — S9 blocked by O1
- [[operator-item__O1|`F` (fixed weekly obligations, min/week) and target `n` (tasks/day, **stated as dispatched]] **blocks** → this — O1 blocks S9
- [[operator-item__O5|Read OpenHands at the pinned SHA]] **blocks** → this — O5 blocks S9
- [[stage__S1|Database foundation]] **blocks** → this — S9 blocked by S1
- [[stage__S2|Oracle environment]] **blocks** → this — S9 blocked by S2
- [[stage__S3|Inspector core]] **blocks** → this — S9 blocked by S3
- [[stage__S4|The two suites, together]] **blocks** → this — S9 blocked by S4
- [[stage__S5|Product path to a reproduced number]] **blocks** → this — S9 blocked by S5
- [[stage__S6|Containment]] **blocks** → this — S9 blocked by S6
- [[stage__S7|Durability]] **blocks** → this — S9 blocked by S7
- [[stage__S8|Deploy and rollback]] **blocks** → this — S9 blocked by S8
