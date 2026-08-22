---
kind: module
id: "module:harness.containment.test_outcome_binding"
title: "The two assertion-outcome enums are bound, though deliberately separate."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/test_outcome_binding.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The two assertion-outcome enums are bound, though deliberately separate."
  - "harness.containment.test_outcome_binding"
generated: true
---

# The two assertion-outcome enums are bound, though deliberately separate.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/test_outcome_binding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/containment/test_outcome_binding.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_containment|harness.containment]] **contains** → this
