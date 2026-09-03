---
kind: module
id: "module:harness.fingerprint.test_factory"
title: "The factory fingerprint, and the two claims about it that a docstring cannot keep true."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/test_factory.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The factory fingerprint, and the two claims about it that a docstring cannot keep true."
  - "harness.fingerprint.test_factory"
generated: true
---

# The factory fingerprint, and the two claims about it that a docstring cannot keep true.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/test_factory.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/fingerprint/test_factory.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — # ACS-1 takes the record type as its domain separator (ADR-0003). Two record types
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """The factory fingerprint, and the two claims about it that a docstring cannot keep true.

The dangerous defect here is
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # ---- the D19 group is one list, not two ------------------------------------------------
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "D19"
