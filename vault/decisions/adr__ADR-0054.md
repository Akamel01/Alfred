---
kind: adr
id: "adr:ADR-0054"
title: "Check A lands: the model that answers is asserted against the fingerprint before an attempt starts"
status: "accepted"
shape: "heading"
date: "2026-09-03"
source: "docs/tier1/adr-log.md:5036"
extractor: "adrs"
aliases:
  - "ADR-0054"
  - "Check A lands: the model that answers is asserted against the fingerprint before an attemp"
generated: true
---

# Check A lands: the model that answers is asserted against the fingerprint before an attempt starts

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:5036`

## Statement

**Date:** 2026-09-03 · **Status:** Accepted · **Supersedes:** none · **Amends:** `docs/tier3/run-instrumentation-specification.md` (provisional) — the `escalation` cause set, `evaluated_at_turn`'s nullability, and two envelope nullability rules · **See also:** ADR-0047 (the prior additive amendment to this document's enums), `docs/tier7/ticket-46-model-routing-decision.md` D6, `scripts/lint_model_routing.py` (check P), #72 · **D28 waiver:** no

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0047|The ownership router gains the factory's facts, and runtime state is never evidence]]

## Enforced by (code)

- **enforced_by** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] — """Check A: the model that answers is the model the fingerprint declared, asserted at start.

Ticket #46 specified two e
- **enforced_by** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] — #: ADR-0054, because none of the eleven existing causes fits: `harness_fault` says this
- **enforced_by** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] — """The `escalation` record a refused start emits.

    Field names are the specification's, not this module's invention:
