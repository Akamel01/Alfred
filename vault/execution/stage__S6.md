---
kind: stage
id: "stage:S6"
title: "Containment"
status: "partial"
shape: "heading"
number: "S6"
source: "docs/tier2/execution-order.md:145"
extractor: "stages"
aliases:
  - "Containment"
  - "S6"
generated: true
---

# Containment

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:145`

## Statement

Containment · *blocks Phase 1 dispatch; blocked by S1* · **PROBES DONE 2026-08-17, enforcement outstanding**

## Fields

| Field | Value |
|---|---|
| `clause` | blocks Phase 1 dispatch; blocked by S1 |
| `completion` | PROBES DONE 2026-08-17, enforcement outstanding |

## Stated in prose — unverified

- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S6
- **blocks** → [[unresolved__phase-1-dispatch|Phase 1 dispatch]] — S6 blocks Phase 1 dispatch
- [[stage__S1|Database foundation]] **blocks** → this — S1 blocks S6
- [[stage__S1|Database foundation]] **blocks** → this — S6 blocked by S1
