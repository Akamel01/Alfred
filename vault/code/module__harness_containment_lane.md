---
kind: module
id: "module:harness.containment.lane"
title: "C11 — the serving lane is the lane the run was dispatched against."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/lane.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C11 — the serving lane is the lane the run was dispatched against."
  - "harness.containment.lane"
generated: true
---

# C11 — the serving lane is the lane the run was dispatched against.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/lane.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/lane.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- **imports** → [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """C11 — the serving lane is the lane the run was dispatched against.

Runs **outside**, against the serving layer. The 
- [[adr__ADR-0017|A containment assertion with an unread premise is a hole, and a hole never passes]] **enforced_by** → this — """C11 — the serving lane is the lane the run was dispatched against.

Runs **outside**, against the serving layer. The 
