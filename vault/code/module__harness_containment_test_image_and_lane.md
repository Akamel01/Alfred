---
kind: module
id: "module:harness.containment.test_image_and_lane"
title: "C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/test_image_and_lane.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls."
  - "harness.containment.test_image_and_lane"
generated: true
---

# C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/test_image_and_lane.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/containment/test_image_and_lane.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_containment_image|C4 — the runtime image is the one the fingerprint declares, and it came from local disk.]]
- **imports** → [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- **imports** → [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]]
- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. A scan that enumerated zero images is the observation a broken probe produces."""
