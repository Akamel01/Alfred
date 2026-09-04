---
kind: module
id: "module:harness.fingerprint.test_attempt_start"
title: "Check A: a planted substitution must refuse to start, and its control must proceed."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/test_attempt_start.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Check A: a planted substitution must refuse to start, and its control must proceed."
  - "harness.fingerprint.test_attempt_start"
generated: true
---

# Check A: a planted substitution must refuse to start, and its control must proceed.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/test_attempt_start.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/fingerprint/test_attempt_start.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- **imports** → [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]]
- **imports** → [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0003|Canonical serialization for hashed structures (ACS-1)]] **enforced_by** → this — """ACS-1 takes the record type as its domain separator (ADR-0003)."""
