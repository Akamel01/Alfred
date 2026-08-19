---
kind: module
id: "module:harness.criterion.execute"
title: "Run a criterion hermetically and classify what happened three ways."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion/execute.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Run a criterion hermetically and classify what happened three ways."
  - "harness.criterion.execute"
generated: true
---

# Run a criterion hermetically and classify what happened three ways.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion/execute.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/criterion/execute.py |
| `tree` | harness |

## Binds

- [[module__harness_criterion|harness.criterion]] **contains** → this
- [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] **imports** → this
- [[module__harness_criterion_test_execute|Three outcomes, and the ways two of them get silently collapsed into one.]] **imports** → this
- [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] **imports** → this
- [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]] **imports** → this
