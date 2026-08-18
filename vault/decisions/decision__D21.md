---
kind: decision
id: "decision:D21"
title: "Alfred designs multi-product, builds single-product"
shape: "table-row"
number: "21"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:65"
extractor: "decisions"
aliases:
  - "Alfred designs multi-product, builds single-product"
  - "D21"
generated: true
---

# Alfred designs multi-product, builds single-product

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:65`

## Statement

**Alfred designs multi-product, builds single-product.** Domain behind ports, real tenancy, per-product policy — but no second product until the first has paying users, and no platform sales.

## Fields

**rationale**

> Forward-compatible at near-zero cost since the invariants already require tenancy. The gate is revenue, not readiness, because "the platform is ready for a second product" is a judgment the platform will always make in its own favour.
