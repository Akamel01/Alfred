---
kind: module
id: "module:harness.containment.image"
title: "C4 — the runtime image is the one the fingerprint declares, and it came from local disk."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/image.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "C4 — the runtime image is the one the fingerprint declares, and it came from local disk."
  - "harness.containment.image"
generated: true
---

# C4 — the runtime image is the one the fingerprint declares, and it came from local disk.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/image.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/image.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_image_and_lane|C4 and C11 — the two rows that were blocked on a fingerprint record, and their controls.]] **imports** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """C4 — the runtime image is the one the fingerprint declares, and it came from local disk.

Runs **outside** the contai
