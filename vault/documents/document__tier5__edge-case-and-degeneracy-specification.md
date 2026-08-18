---
kind: document
id: "document:tier5/edge-case-and-degeneracy-specification"
title: "Edge Case and Degeneracy Specification"
status: "frozen"
shape: "file"
owner: "human"
enforcement: "ci-gate"
tier: "5"
written: "full"
review_after: "Phase 1"
source: "docs/tier5/edge-case-and-degeneracy-specification.md:1"
extractor: "documents"
tags: [ci-gate, human, tier5]
aliases:
  - "Edge Case and Degeneracy Specification"
  - "tier5/edge-case-and-degeneracy-specification"
generated: true
---

# Edge Case and Degeneracy Specification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier5/edge-case-and-degeneracy-specification.md:1`

## Falsifies if

> A metric returns a finite number for an input this document declares undefined, or returns NaN anywhere, or a case observed in real scenario data appears nowhere in this catalog.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier5/edge-case-and-degeneracy-specification.md |
| `tier_name` | Product |

**evidence**

> The oracle's own regression suite asserts `0.0` or `inf` for several measures, which is why those measures were excluded from the verified task class — a test pinning a sentinel is not evidence the metric computes. Degenerate geometry is also where a wrong number is least likely to throw and most likely to look plausible.

## Binds

- [[tier__tier5|Tier 5 — Product]] **contains** → this
