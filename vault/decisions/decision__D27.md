---
kind: decision
id: "decision:D27"
title: "all in Phase 0"
shape: "table-row"
number: "27"
source: "plan/handoff-autonomous-software-engineering-fizzy-dahl.md:71"
extractor: "decisions"
aliases:
  - "D27"
  - "all in Phase 0"
generated: true
---

# all in Phase 0

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `plan/handoff-autonomous-software-engineering-fizzy-dahl.md:71`

## Statement

**Result provenance, recall protocol, and published validity envelopes — all in Phase 0.** Every emitted result carries metric version, code commit, assumption set, input hash, and tolerance. Defects trigger a versioned advisory naming affected versions and date ranges. Each metric ships a validity envelope in its model card.

## Fields

**rationale**

> A wrong risk number is not an outage: it does not throw, spike latency, or fail a healthcheck. Every observability mechanism in this plan detects a different class of failure. Remediation therefore has to carry the load, and remediation needs stamping that **cannot be retrofitted** — results computed before it exists are permanently unrecallable. The advisory model works without holding customer data, so it stays compatible with a customer-deployed product.

## Enforced by (code)

- **enforced_by** → [[module__migrations_product_versions_0001_product_base|product: scenarios, trajectories, metric results, result stamps.]] — """product: scenarios, trajectories, metric results, result stamps.

Revision ID: 0001_product_base
Revises:
Create Date
