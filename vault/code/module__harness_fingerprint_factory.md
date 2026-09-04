---
kind: module
id: "module:harness.fingerprint.factory"
title: "The factory fingerprint: what an *agent* run was measured on, as opposed to a lane."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/factory.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The factory fingerprint: what an *agent* run was measured on, as opposed to a lane."
  - "harness.fingerprint.factory"
generated: true
---

# The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/factory.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/fingerprint/factory.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this
- [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] **imports** → this
- [[module__harness_fingerprint_test_attempt_start|Check A: a planted substitution must refuse to start, and its control must proceed.]] **imports** → this
- [[module__harness_fingerprint_test_factory|The factory fingerprint, and the two claims about it that a docstring cannot keep true.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — #: record type as its domain separator (ADR-0003), so a factory record and a lane record
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.

`RunFingerprint` cannot describe
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — #: Taken from `RunFingerprint` rather than retyped. The D19 group has one definition.
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "D19"
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "D19"
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # D19 — shared verbatim with RunFingerprint.
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """The D19 group here is the D19 group there — checked, not asserted in a comment.

    `record.py` owns the list. If a 
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "D19"
- [[decision__D20|Agents may improve the factory, never the inspector]] **enforced_by** → this — """The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.

`RunFingerprint` cannot describe
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.

`RunFingerprint` cannot describe
