---
kind: module
id: "module:harness.criterion.materialize"
title: "Build the criterion environment from an allowlist, never from the candidate tree."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion/materialize.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Build the criterion environment from an allowlist, never from the candidate tree."
  - "harness.criterion.materialize"
generated: true
---

# Build the criterion environment from an allowlist, never from the candidate tree.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion/materialize.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/criterion/materialize.py |
| `tree` | harness |

## Binds

- [[module__harness_criterion|harness.criterion]] **contains** → this
- [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] **imports** → this
- [[module__harness_criterion_test_materialize|A1, asserted as an architectural claim rather than as a list of blocked filenames.]] **imports** → this
- [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] **imports** → this
- [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]] **imports** → this
- [[module__harness_selftest_test_selftest|S4. The inspector's inspector, and the controls that stop it reading green for free.]] **imports** → this
