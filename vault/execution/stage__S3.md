---
kind: stage
id: "stage:S3"
title: "Inspector core"
status: "done"
shape: "heading"
number: "S3"
source: "docs/tier2/execution-order.md:132"
extractor: "stages"
aliases:
  - "Inspector core"
  - "S3"
generated: true
---

# Inspector core

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:132`

## Statement

Inspector core · *blocks S4, and every verdict ever recorded* · **DONE 2026-08-17**

## Fields

| Field | Value |
|---|---|
| `clause` | blocks S4, and every verdict ever recorded |
| `completion` | DONE 2026-08-17 |

## Stated in prose — unverified

- **blocks** → [[stage__S4|The two suites, together]] — S3 blocks S4
- **blocks** → [[stage__S4|The two suites, together]] — S4 blocked by S3
- **blocks** → [[stage__S9|Phase 1 build]] — S9 blocked by S3
- [[stage__S1|Database foundation]] **blocks** → this — S1 blocks S3
