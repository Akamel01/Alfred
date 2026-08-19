---
kind: module
id: "module:harness.selftest.suites"
title: "The two suites. They are one module because they are each other's vacuity control."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest/suites.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The two suites. They are one module because they are each other's vacuity control."
  - "harness.selftest.suites"
generated: true
---

# The two suites. They are one module because they are each other's vacuity control.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest/suites.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/selftest/suites.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_execute|Run a criterion hermetically and classify what happened three ways.]]
- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **imports** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]]
- **imports** → [[module__harness_selftest_noise|Measures ε. It is never chosen, and this is the module that makes that true.]]
- **imports** → [[module__harness_selftest_synthetic|A criterion with no domain in it, and a defect that can be dialled.]]
- [[module__harness_selftest|harness.selftest]] **contains** → this
- [[module__harness_selftest_test_selftest|S4. The inspector's inspector, and the controls that stop it reading green for free.]] **imports** → this
