---
kind: stage
id: "stage:S5"
title: "Product path to a reproduced number"
status: "not-started"
shape: "heading"
number: "S5"
source: "docs/tier2/execution-order.md:199"
extractor: "stages"
aliases:
  - "Product path to a reproduced number"
  - "S5"
generated: true
---

# Product path to a reproduced number

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:199`

## Statement

Product path to a reproduced number · *blocks Phase 0 exit; blocked by S1, S2*

## Fields

| Field | Value |
|---|---|
| `clause` | blocks Phase 0 exit; blocked by S1, S2 |

## Stated in prose — unverified

- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S5
- **blocks** → [[unresolved__phase-0-exit|Phase 0 exit]] — S5 blocks Phase 0 exit
- [[stage__S1|Database foundation]] **blocks** → this — S5 blocked by S1
- [[stage__S2|Oracle environment]] **blocks** → this — S2 blocks S5
- [[stage__S2|Oracle environment]] **blocks** → this — S5 blocked by S2
