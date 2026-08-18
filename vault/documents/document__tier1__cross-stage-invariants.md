---
kind: document
id: "document:tier1/cross-stage-invariants"
title: "Cross-Stage Invariants"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "1"
written: "full"
review_after: "Phase 2"
source: "docs/tier1/cross-stage-invariants.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier1]
aliases:
  - "Cross-Stage Invariants"
  - "tier1/cross-stage-invariants"
generated: true
---

# Cross-Stage Invariants

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/cross-stage-invariants.md:1`

## Falsifies if

> An invariant is found violated in merged code, meaning the CI lint does not actually enforce what this document claims.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/cross-stage-invariants.md |
| `tier_name` | Architecture |

**evidence**

> Each invariant is included because its retrofit cost is a migration or a rewrite, and several are the specific omissions that made a prior attempt expensive to correct.

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
