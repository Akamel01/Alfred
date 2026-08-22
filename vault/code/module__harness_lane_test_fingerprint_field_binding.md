---
kind: module
id: "module:harness.lane.test_fingerprint_field_binding"
title: "Three spellings of \"the lane's fields\", and the two-schema reality between them."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/lane/test_fingerprint_field_binding.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Three spellings of \"the lane's fields\", and the two-schema reality between them."
  - "harness.lane.test_fingerprint_field_binding"
generated: true
---

# Three spellings of "the lane's fields", and the two-schema reality between them.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/lane/test_fingerprint_field_binding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/lane/test_fingerprint_field_binding.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- **imports** → [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]]
- [[module__harness_lane|harness.lane]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0020|The run fingerprint record, and the two assertions that were waiting on it]] **enforced_by** → this — """Three spellings of "the lane's fields", and the two-schema reality between them.

`harness/fingerprint/record.py` `FI
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Vacuity guard (D57): empty groups agree with anything and pin nothing."""
