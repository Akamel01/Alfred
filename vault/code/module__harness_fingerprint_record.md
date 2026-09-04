---
kind: module
id: "module:harness.fingerprint.record"
title: "The run fingerprint record: what a run was measured on, stated once and hashed."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/fingerprint/record.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The run fingerprint record: what a run was measured on, stated once and hashed."
  - "harness.fingerprint.record"
generated: true
---

# The run fingerprint record: what a run was measured on, stated once and hashed.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/fingerprint/record.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/fingerprint/record.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_acs_acs1|ACS-1 — Alfred Canonical Serialization, version 1 (ADR-0003, ADR-0004).]]
- [[module__harness_fingerprint|harness.fingerprint]] **contains** → this
- [[module__harness_containment_image|C4 — the runtime image is the one the fingerprint declares, and it came from local disk.]] **imports** → this
- [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]] **imports** → this
- [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] **imports** → this
- [[module__harness_fingerprint_attempt_start|Check A: the model that answers is the model the fingerprint declared, asserted at start.]] **imports** → this
- [[module__harness_fingerprint_factory|The factory fingerprint: what an *agent* run was measured on, as opposed to a lane.]] **imports** → this
- [[module__harness_fingerprint_test_factory|The factory fingerprint, and the two claims about it that a docstring cannot keep true.]] **imports** → this
- [[module__harness_fingerprint_test_record|The run fingerprint record, and the control that the hash covers every field.]] **imports** → this
- [[module__harness_lane_lane_fingerprint|Fail-closed fingerprint assertion for the inference lane (D19/D40).]] **imports** → this
- [[module__harness_lane_test_fingerprint_field_binding|Three spellings of "the lane's fields", and the two-schema reality between them.]] **imports** → this
- [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]] **imports** → this
- [[module__harness_worker_test_fake|Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.]] **imports** → this
- [[module__scripts_capture_run_fingerprint|Factory-owned script that collects all RunFingerprint fields from live sources,]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0018|The executor moved, and eleven of thirteen premises were wrong]] **enforced_by** → this — """The run fingerprint record: what a run was measured on, stated once and hashed.

Two containment assertions could not
- [[adr__ADR-0019|D38's sandbox rationale, verified: true of one configuration, false of the default]] **enforced_by** → this — """The run fingerprint record: what a run was measured on, stated once and hashed.

Two containment assertions could not
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # D19: what tiered requalification reads to decide which component moved.
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — "D19"
- [[decision__D19|Autonomy grants are keyed to a fingerprint]] **enforced_by** → this — # D19.
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — # D40: the fields a measurement is not comparable across.
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — "D40"
- [[decision__D40|fingerprint extension (final form)]] **enforced_by** → this — # D40. The quantization *artifact* hash, never the quant name — imatrix variants share
