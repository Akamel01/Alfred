---
kind: document
id: "document:tier1/cross-stage-invariants"
title: "Cross-Stage Invariants"
status: "provisional"
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

> An invariant is found violated in merged code, meaning its stated holder — lint or review — does not actually hold it; or this document describes an invariant as lint-held when scripts/lint_invariants.py's ENFORCEMENT map says review, or the reverse, meaning the description drifted from the code that is the authority.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/cross-stage-invariants.md |
| `tier_name` | Architecture |

**evidence**

> Each invariant is included because its retrofit cost is a migration or a rewrite, and several are the specific omissions that made a prior attempt expensive to correct. Reclassified from frozen by ADR-0064, applying ADR-0063's lesson before a third waiver rather than after: what enforces which invariant moves as enforcement is built out, and a frozen document cannot follow that without a waiver each time. The invariants themselves are the commitment; the enforcement map is what moves.

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
