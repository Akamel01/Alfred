---
kind: document
id: "document:tier7/ticket-47-edge-semantics-decision"
title: "Ticket #47 — execution edge semantics"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "Phase 2"
source: "docs/tier7/ticket-47-edge-semantics-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #47 — execution edge semantics"
  - "tier7/ticket-47-edge-semantics-decision"
generated: true
---

# Ticket #47 — execution edge semantics

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-47-edge-semantics-decision.md:1`

## Falsifies if

> An edge kind rejected here is later needed to answer a question no existing edge answers; or the type graph is found being executed rather than validated against.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-47-edge-semantics-decision.md |
| `tier_name` | Meta |

**evidence**

> A read of policy/node-palette.json's port declarations, orchestration/topology.json as it stands (8 nodes, 7 edges), lint_topology.py's TOP003-TOP005 port-compatibility rule, and the nine edge kinds proposed in the brief's §8. The proposed topology in D4 was verified by running check_topology against a candidate tree, not asserted.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
