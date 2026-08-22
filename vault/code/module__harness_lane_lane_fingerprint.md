---
kind: module
id: "module:harness.lane.lane_fingerprint"
title: "Fail-closed fingerprint assertion for the inference lane (D19/D40)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/lane/lane_fingerprint.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Fail-closed fingerprint assertion for the inference lane (D19/D40)."
  - "harness.lane.lane_fingerprint"
generated: true
---

# Fail-closed fingerprint assertion for the inference lane (D19/D40).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/lane/lane_fingerprint.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/lane/lane_fingerprint.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_lane|harness.lane]] **contains** → this
- [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]] **imports** → this
- [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] **imports** → this
- [[module__harness_lane_test_fingerprint_field_binding|Three spellings of "the lane's fields", and the two-schema reality between them.]] **imports** → this

## Enforced by (code)

- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — """Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — """Fail-closed fingerprint assertion for the inference lane (D19/D40).

The serving stack auto-unloads an idle model and
