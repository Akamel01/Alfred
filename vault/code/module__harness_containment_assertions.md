---
kind: module
id: "module:harness.containment.assertions"
title: "Three outcomes for a containment assertion, and the third is the dangerous one."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/assertions.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Three outcomes for a containment assertion, and the third is the dangerous one."
  - "harness.containment.assertions"
generated: true
---

# Three outcomes for a containment assertion, and the third is the dangerous one.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/assertions.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/assertions.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_egress|C6 — the egress canary, and the control that stops it being vacuous.]] **imports** → this
- [[module__harness_containment_handle|The one crossing from probe vocabulary to handle vocabulary.]] **imports** → this
- [[module__harness_containment_image|C4 — the runtime image is the one the fingerprint declares, and it came from local disk.]] **imports** → this
- [[module__harness_containment_inside|C8, C9, C12, C13 — the assertions that need no executor vocabulary.]] **imports** → this
- [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]] **imports** → this
- [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]] **imports** → this
- [[module__harness_containment_patch_side|C15 — the oracle arriving through the deliverable channel.]] **imports** → this
- [[module__harness_containment_reassert|C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.]] **imports** → this
- [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]] **imports** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this
- [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]] **imports** → this
- [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Three outcomes for a containment assertion, and the third is the dangerous one.

`passed` and `failed` are obvious. *
