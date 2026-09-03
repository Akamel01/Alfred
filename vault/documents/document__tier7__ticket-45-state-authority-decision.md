---
kind: document
id: "document:tier7/ticket-45-state-authority-decision"
title: "Ticket #45 — state authority: decision record"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the first factory task that emits run records"
source: "docs/tier7/ticket-45-state-authority-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #45 — state authority: decision record"
  - "tier7/ticket-45-state-authority-decision"
generated: true
---

# Ticket #45 — state authority: decision record

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-45-state-authority-decision.md:1`

## Falsifies if

> A fact in the homes table below is written authoritatively in two places; or a gate, verdict or audit is observed reading machine-local runtime state.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-45-state-authority-decision.md |
| `tier_name` | Meta |

**evidence**

> A grilling session on 2026-09-02 against data-architecture.md (frozen), cross-stage-invariants.md, run-instrumentation-specification.md, ECC's state-store.schema.json, and the .autoforge/state.json produced by a real AutoForge run against this repository on 2026-08-29. No factory task has yet written a run record; nothing here rests on an observed write.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
