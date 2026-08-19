---
kind: module
id: "module:harness.stamp"
title: "harness.stamp"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/stamp:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.stamp"
generated: true
---

# harness.stamp

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/stamp:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_stamp___init__|Inspector-side reading of product result stamps.]]
- **contains** → [[module__harness_stamp_test_verdict_map|The verdict table's own tests, including its vacuity control.]]
- **contains** → [[module__harness_stamp_verdict_map|ADR-0006's verdict table, as data rather than as prose.]]
- [[gate-step__inspector_14|Stamp (version, upstream union, total verifier)]] **runs** → this
