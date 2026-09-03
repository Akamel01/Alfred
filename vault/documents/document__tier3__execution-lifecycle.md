---
kind: document
id: "document:tier3/execution-lifecycle"
title: "Execution Lifecycle"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "review-cadence"
tier: "3"
written: "full"
review_after: "the first ten tasks that walk it"
source: "docs/tier3/execution-lifecycle.md:1"
extractor: "documents"
tags: [human, review-cadence, tier3]
aliases:
  - "Execution Lifecycle"
  - "tier3/execution-lifecycle"
generated: true
---

# Execution Lifecycle

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier3/execution-lifecycle.md:1`

## Falsifies if

> A task completes the seven phases and the merge gate still catches a class of defect this lifecycle claims to prevent upstream; or the front half is observed to be skipped without the task class declaring it; or a re-entry sends work downstream of the static default.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier3/execution-lifecycle.md |
| `tier_name` | Agent specifications |

**evidence**

> The decisions in docs/tier7/ticket-42-execution-lifecycle-decision.md, taken against the Definition of Done's twelve conditions, failure-semantics' three-valued verdict, AutoForge's protocol.md and stages/ directory, and the ECC capability audit. No task has walked these seven phases end to end; the phase set rests on a reduction of AutoForge's twelve names, not on observed execution.

## Binds

- [[tier__tier3|Tier 3 — Agent specifications]] **contains** → this
