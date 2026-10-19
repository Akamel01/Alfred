---
kind: document
id: "document:tier7/ticket-70-measurement-design"
title: "Ticket #70 — Measurement design for the trivial class"
status: "directional"
shape: "file"
owner: "executable"
enforcement: "review-cadence"
tier: "7"
written: "full"
review_after: "Phase 2"
source: "docs/tier7/ticket-70-measurement-design.md:1"
extractor: "documents"
tags: [executable, review-cadence, tier7]
aliases:
  - "Ticket #70 — Measurement design for the trivial class"
  - "tier7/ticket-70-measurement-design"
generated: true
---

# Ticket #70 — Measurement design for the trivial class

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier7/ticket-70-measurement-design.md:1`

## Falsifies if

> A capability enters the trivial class on a run whose fingerprint does not match the pair this document states for the arm that produced it, or a merge rate taken under this protocol is read as a point estimate rather than a Wilson 95% interval, or a run starts while docs/tier2/execution-order.md:424 still forbids orchestration.

## Fields

| Field | Value |
|---|---|
| `path` | docs/tier7/ticket-70-measurement-design.md |
| `tier_name` | Meta |

**evidence**

> Reads policy/model-routing.json (the empty trivial class and the forbidden list), policy/role-bindings.json (the 24 unset D19 version fields), harness/fingerprint/factory.py (the 11-field record), docs/tier3/run-instrumentation-specification.md (attempt_start, attempt_end, task_end), docs/tier0/charter-and-non-goals.md K3, and docs/tier2/execution-order.md:424. No measurement of any model against any Alfred capability exists; this document specifies the measurement rather than reporting one.

## Binds

- [[tier__tier7|Tier 7 — Meta]] **contains** → this
