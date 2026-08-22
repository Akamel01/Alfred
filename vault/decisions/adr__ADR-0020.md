---
kind: adr
id: "adr:ADR-0020"
title: "The run fingerprint record, and the two assertions that were waiting on it"
status: "accepted"
shape: "heading"
date: "2026-08-19"
source: "docs/tier1/adr-log.md:1951"
extractor: "adrs"
aliases:
  - "ADR-0020"
  - "The run fingerprint record, and the two assertions that were waiting on it"
generated: true
---

# The run fingerprint record, and the two assertions that were waiting on it

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `docs/tier1/adr-log.md:1951`

## Statement

**Date:** 2026-08-19 · **Status:** Accepted · **Supersedes:** none · **Amends:** the Sandbox Specification's C4 and C11 rows; the `Worker` port's fingerprint obligations · **See also:** ADR-0018 and ADR-0019 (which both recorded C4 and C11 as blocked on this), ADR-0017 (shells and why a green assertion can be worse than an absent one), ADR-0007 (the vacuity class), D19 and D40 (the field set)

## Fields

| Field | Value |
|---|---|
| `status_raw` | Accepted |

## Binds

- **see_also** → [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]]
- **see_also** → [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]]
- **see_also** → [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]]
- **see_also** → [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]]

## Enforced by (code)

- **enforced_by** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]] — """Containment assertions: what the sandbox must prove before a run starts.

Inspector machinery (D20). Every assertion 
- **enforced_by** → [[module__harness_fingerprint___init__|The run fingerprint record — the declared configuration a run is measured on.]] — """The run fingerprint record — the declared configuration a run is measured on.

Inspector machinery (D20). `record.py`
- **enforced_by** → [[module__harness_lane_test_fingerprint_field_binding|Three spellings of "the lane's fields", and the two-schema reality between them.]] — """Three spellings of "the lane's fields", and the two-schema reality between them.

`harness/fingerprint/record.py` `FI
- **enforced_by** → [[module__migrations_harness_control_versions_0002_fingerprint_run_fields|control: the run-fingerprint fields the register had no column for.]] — """control: the run-fingerprint fields the register had no column for.

Revision ID: 0002_fingerprint_run_fields
Revises
