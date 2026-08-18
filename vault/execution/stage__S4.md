---
kind: stage
id: "stage:S4"
title: "The two suites, together"
status: "not-started"
shape: "heading"
number: "S4"
source: "docs/tier2/execution-order.md:123"
extractor: "stages"
aliases:
  - "S4"
  - "The two suites, together"
generated: true
---

# The two suites, together

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:123`

## Statement

The two suites, together · *blocks Phase 0 exit; blocked by S1, S2, S3*

## Fields

| Field | Value |
|---|---|
| `clause` | blocks Phase 0 exit; blocked by S1, S2, S3 |

## Stated in prose — unverified

- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S4
- **blocks** → [[unresolved__phase-0-exit|Phase 0 exit]] — S4 blocks Phase 0 exit
- [[stage__S1|Database foundation]] **blocks** → this — S1 blocks S4
- [[stage__S1|Database foundation]] **blocks** → this — S4 blocked by S1
- [[stage__S2|Oracle environment]] **blocks** → this — S2 blocks S4
- [[stage__S2|Oracle environment]] **blocks** → this — S4 blocked by S2
- [[stage__S3|Inspector core]] **blocks** → this — S3 blocks S4
- [[stage__S3|Inspector core]] **blocks** → this — S4 blocked by S3
