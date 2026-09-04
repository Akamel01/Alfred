---
kind: module
id: "module:harness.fingerprint.attempt_start"
title: "Check A: the model that answers is the model the fingerprint declared, asserted at start."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/attempt_start.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Check A: the model that answers is the model the fingerprint declared, asserted at start."
  - "harness.fingerprint.attempt_start"
generated: true
---

# Check A: the model that answers is the model the fingerprint declared, asserted at start.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/attempt_start.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/fingerprint/attempt_start.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this
- [[module__harness_fingerprint_test_attempt_start|Check A: a planted substitution must refuse to start, and its control must proceed.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — #: ACS-1 takes the record type as its domain separator (ADR-0003): a bundle and a
- [[adr__ADR-0054|Check A lands: the model that answers is asserted against the fingerprint before an attemp]] **enforced_by** → this — """Check A: the model that answers is the model the fingerprint declared, asserted at start.

Ticket #46 specified two e
- [[adr__ADR-0054|Check A lands: the model that answers is asserted against the fingerprint before an attemp]] **enforced_by** → this — #: ADR-0054, because none of the eleven existing causes fits: `harness_fault` says this
- [[adr__ADR-0054|Check A lands: the model that answers is asserted against the fingerprint before an attemp]] **enforced_by** → this — """The `escalation` record a refused start emits.

    Field names are the specification's, not this module's invention:
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """Check A: the model that answers is the model the fingerprint declared, asserted at start.

Ticket #46 specified two e
