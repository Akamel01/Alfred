---
kind: stage
id: "stage:S2"
title: "Oracle environment"
status: "partial"
shape: "heading"
number: "S2"
source: "docs/tier2/execution-order.md:88"
extractor: "stages"
aliases:
  - "Oracle environment"
  - "S2"
generated: true
---

# Oracle environment

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:88`

## Statement

Oracle environment · *blocks S5's reference values and the D49 P3 decision* · **ENVIRONMENT DONE 2026-08-18**

## Fields

| Field | Value |
|---|---|
| `clause` | blocks S5's reference values and the D49 P3 decision |
| `completion` | ENVIRONMENT DONE 2026-08-18 |

## Stated in prose — unverified

- **blocks** → [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] — S2 blocks D49
- **blocks** → [[stage__S5|Product path to a reproduced number]] — S2 blocks S5
- **blocks** → [[stage__S5|Product path to a reproduced number]] — S5 blocked by S2
- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S2
- [[operator-item__O3|D49 P3: validate, or take the stated degradation to the 10 strong P1 measures]] **blocks** → this — O3 blocks S2
