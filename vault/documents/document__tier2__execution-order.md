---
kind: document
id: "document:tier2/execution-order"
title: "Execution Order"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "review-cadence"
tier: "2"
written: "full"
review_after: "Phase 0 exit"
source: "docs/tier2/execution-order.md:1"
extractor: "documents"
tags: [human, review-cadence, tier2]
aliases:
  - "Execution Order"
  - "tier2/execution-order"
generated: true
---

# Execution Order

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/execution-order.md:1`

## Falsifies if

> Any stage below is completed out of the stated order without a waiver ADR and the stage it was said to block proceeds unaffected — meaning the dependency was asserted rather than real.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/execution-order.md |
| `tier_name` | Build protocol |

**evidence**

> Derived from the eight completed handoffs (H1–H8) and a repository inventory verified 2026-08-17. Every "does not exist" below was checked against the filesystem, not recalled.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
