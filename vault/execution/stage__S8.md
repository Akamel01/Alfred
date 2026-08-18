---
kind: stage
id: "stage:S8"
title: "Deploy and rollback"
status: "not-started"
shape: "heading"
number: "S8"
source: "docs/tier2/execution-order.md:190"
extractor: "stages"
aliases:
  - "Deploy and rollback"
  - "S8"
generated: true
---

# Deploy and rollback

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:190`

## Statement

Deploy and rollback · *blocks Phase 0 exit*

## Fields

| Field | Value |
|---|---|
| `clause` | blocks Phase 0 exit |

## Stated in prose — unverified

- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S8
- **blocks** → [[unresolved__phase-0-exit|Phase 0 exit]] — S8 blocks Phase 0 exit
