---
kind: document
id: "document:tier2/definition-of-done"
title: "Definition of Done"
status: "frozen"
shape: "file"
owner: "executable"
enforcement: "ci-gate"
tier: "2"
written: "full"
review_after: "Phase 2"
source: "docs/tier2/definition-of-done.md:1"
extractor: "documents"
tags: [ci-gate, executable, tier2]
aliases:
  - "Definition of Done"
  - "tier2/definition-of-done"
generated: true
---

# Definition of Done

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier2/definition-of-done.md:1`

## Falsifies if

> A change merges with any condition below unmet, or a defect reaches merge that one of these conditions would have caught.

## Fields

| Field | Value |
|---|---|
| `evidence` | Each condition corresponds to a control this architecture depends on. The pre-review scan exists because CI runs before any human sees a pull request, so review is not the first gate. |
| `path` | docs/tier2/definition-of-done.md |
| `tier_name` | Build protocol |

## Binds

- [[tier__tier2|Tier 2 — Build protocol]] **contains** → this
