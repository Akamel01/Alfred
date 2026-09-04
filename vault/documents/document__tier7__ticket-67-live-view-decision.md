---
kind: document
id: "document:tier7/ticket-67-live-view-decision"
title: "Ticket #67 — the live multi-agent view"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the first screen that exists"
source: "docs/tier7/ticket-67-live-view-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #67 — the live multi-agent view"
  - "tier7/ticket-67-live-view-decision"
generated: true
---

# Ticket #67 — the live multi-agent view

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-67-live-view-decision.md:1`

## Falsifies if

> Agent-stated intent is found on S2 or cited by a gate; or the live view and Part B become visually indistinguishable; or an operator watches a run overrun with no action available.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-67-live-view-decision.md |
| `tier_name` | Meta |

**evidence**

> Six requirements given by the operator on 2026-09-03, read against mission-control-specification.md (the boundary split, the read-model no-cache rule, the deliberately-hard-to-reach list, Part B, the deferred table, and authentication and exposure), ADR-0047, and the handoff contract graduated the same day. No Mission Control code exists; nothing here rests on an observed render.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
