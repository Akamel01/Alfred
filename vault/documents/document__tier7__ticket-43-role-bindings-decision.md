---
kind: document
id: "document:tier7/ticket-43-role-bindings-decision"
title: "Ticket #43 — role bindings: decision record"
status: "provisional"
shape: "file"
owner: "human"
enforcement: "none"
tier: "7"
written: "full"
review_after: "the first task dispatched through a binding"
source: "docs/tier7/ticket-43-role-bindings-decision.md:1"
extractor: "documents"
tags: [human, none, tier7]
aliases:
  - "Ticket #43 — role bindings: decision record"
  - "tier7/ticket-43-role-bindings-decision"
generated: true
---

# Ticket #43 — role bindings: decision record

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-43-role-bindings-decision.md:1`

## Falsifies if

> A palette kind of category `operator` acquires a runtime binding; or a binding record's model is resolved from anywhere other than the routing policy; or a binding is edited without a requalification following.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-43-role-bindings-decision.md |
| `tier_name` | Meta |

**evidence**

> A grilling session on 2026-09-02 against policy/node-palette.json (21 kinds), the three Tier 3 agent stubs, harness/fingerprint/record.py's D19 group, scripts/lint_topology.py, and the 68 ECC agent definitions installed to ~/.claude/agents on the same day. No palette kind has yet dispatched work; no binding has been exercised.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
