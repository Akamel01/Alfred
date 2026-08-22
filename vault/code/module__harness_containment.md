---
kind: module
id: "module:harness.containment"
title: "harness.containment"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.containment"
generated: true
---

# harness.containment

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_containment___init__|Containment assertions: what the sandbox must prove before a run starts.]]
- **contains** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **contains** → [[module__harness_containment_denylist|Load the oracle denylist and give it a digest the fingerprint can carry.]]
- **contains** → [[module__harness_containment_egress|C6 — the egress canary, and the control that stops it being vacuous.]]
- **contains** → [[module__harness_containment_handle|The one crossing from probe vocabulary to handle vocabulary.]]
- **contains** → [[module__harness_containment_image|C4 — the runtime image is the one the fingerprint declares, and it came from local disk.]]
- **contains** → [[module__harness_containment_inside|C8, C9, C12, C13 — the assertions that need no executor vocabulary.]]
- **contains** → [[module__harness_containment_lane|C11 — the serving lane is the lane the run was dispatched against.]]
- **contains** → [[module__harness_containment_oracle_absence|C7 — the oracle is absent, asserted rather than assumed.]]
- **contains** → [[module__harness_containment_patch_side|C15 — the oracle arriving through the deliverable channel.]]
- **contains** → [[module__harness_containment_reassert|C14 — the end-of-run re-assertion, and why a boot-time pass is not enough.]]
- **contains** → [[module__harness_containment_shells|The executor-premise assertions, and the source read that filled their holes (O5).]]
- **contains** → [[module__harness_containment_source_hashes|The register C15 clause 3 compares against, and the reason it had nothing to compare.]]
- **contains** → [[module__harness_containment_test_archive_suffix_binding|Two ARCHIVE_SUFFIXES tuples, frozen verbatim, because their split is real and unexplained.]]
- **contains** → [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]]
- **contains** → [[module__harness_containment_test_containment|Containment assertions, each paired with the control that stops it reading green.]]
- **contains** → [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]]
- **contains** → [[module__harness_containment_test_outcome_binding|The two assertion-outcome enums are bound, though deliberately separate.]]
- [[gate-step__inspector_08|Containment (C6, C7 probes; C8-C15; and the O5 shells that must not pass)]] **runs** → this
