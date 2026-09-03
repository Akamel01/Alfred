---
kind: document
id: "document:tier7/ticket-44-task-contract-decision"
title: "Ticket #44 — the canonical task contract"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "Phase 2"
source: "docs/tier7/ticket-44-task-contract-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #44 — the canonical task contract"
  - "tier7/ticket-44-task-contract-decision"
generated: true
---

# Ticket #44 — the canonical task contract

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-44-task-contract-decision.md:1`

## Falsifies if

> A third document is found describing what an agent is handed; or a factory run is found crossing the Worker port, meaning D2 drew the boundary in the wrong place.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-44-task-contract-decision.md |
| `tier_name` | Meta |

**evidence**

> A read of the frozen task specification standard, the Worker port contract's WorkerSpec, the handoff contract stub, and AutoForge's spawn-contract.md, against the FactoryFingerprint added in this effort. No task has been dispatched through the contracts named here; the seam is read off documents that already bind, not off an observed dispatch.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
