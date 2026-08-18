---
kind: document
id: "document:tier1/mission-control-specification"
title: "Mission Control Specification"
status: "provisional"
shape: "file"
owner: "executable"
enforcement: "schema"
tier: "1"
written: "full"
review_after: "Phase 1"
source: "docs/tier1/mission-control-specification.md:1"
extractor: "documents"
tags: [executable, schema, tier1]
aliases:
  - "Mission Control Specification"
  - "tier1/mission-control-specification"
generated: true
---

# Mission Control Specification

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/mission-control-specification.md:1`

## Falsifies if

> A Phase 1 merge is authorized without a corresponding operator-action row in the evidence chain; or the capacity ledger cannot be computed from recorded review time because the recorded number is dominated by tab-open wall clock rather than attended time; or criterion-first ordering is observed not to hold — reviewers open the full diff on a majority of tasks with no anomaly flag set.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier1/mission-control-specification.md |
| `tier_name` | Architecture |

**evidence**

> The surface's obligations are derived from controls that already exist — three-valued verdicts (Failure Semantics), the run record stream's `task_end.human_review_ms` field, which is specified as "recorded from the review interaction, not estimated" and today has no instrument, and the capacity ledger's requirement for human minutes per task. Nothing here rests on an observed review: no review has happened.

## Binds

- [[tier__tier1|Tier 1 — Architecture]] **contains** → this
