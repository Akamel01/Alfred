---
kind: module
id: "module:harness.stamp.test_verdict_map"
title: "The verdict table's own tests, including its vacuity control."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/stamp/test_verdict_map.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The verdict table's own tests, including its vacuity control."
  - "harness.stamp.test_verdict_map"
generated: true
---

# The verdict table's own tests, including its vacuity control.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/stamp/test_verdict_map.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/stamp/test_verdict_map.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_stamp_verdict_map|ADR-0006's verdict table, as data rather than as prose.]]
- [[module__harness_stamp|harness.stamp]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The five rows ADR-0006 specifies, restated here rather than read from the module under
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """D57. A mapping with no rows would pass every row-wise test below for free."""
