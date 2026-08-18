---
kind: document
id: "document:tier2/testing-strategy"
title: "Testing Strategy"
status: "frozen"
shape: "file"
owner: "human"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 2"
source: "docs/tier2/testing-strategy.md:1"
extractor: "documents"
tags: [ci-gate, human, tier2]
aliases:
  - "Testing Strategy"
  - "tier2/testing-strategy"
generated: true
---

# Testing Strategy

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/testing-strategy.md:1`

## Falsifies if

> A composed property test is found that an agent could satisfy by special-casing, or held-out pass rate tracks visible pass rate across a full golden set.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier2/testing-strategy.md |
| `tier_name` | Build protocol |

**evidence**

> The visible/held-out split addresses a measured 43-48pp gap on composed operations with no exploit involved. The exclusion of mutation score follows a replication finding that mutation scores are meaningless in a bug-detection setting.

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
