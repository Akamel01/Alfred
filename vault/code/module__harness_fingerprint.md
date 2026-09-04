---
kind: module
id: "module:harness.fingerprint"
title: "harness.fingerprint"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.fingerprint"
generated: true
---

# harness.fingerprint

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_fingerprint___init__|The run fingerprint record — the declared configuration a run is measured on.]]
- **contains** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]]
- **contains** → [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]]
- **contains** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- **contains** → [[module__harness_fingerprint_test_attempt_start|Check A: a planted substitution must refuse to start, and its control must proceed.]]
- **contains** → [[module__harness_fingerprint_test_factory|The factory fingerprint, and the two claims about it that a docstring cannot keep true.]]
- **contains** → [[module__harness_fingerprint_test_record|The run fingerprint record, and the control that the hash covers every field.]]
- [[gate-step__inspector_15|Run fingerprint record (field set, derived digest, register agreement)]] **runs** → this
