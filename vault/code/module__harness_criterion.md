---
kind: module
id: "module:harness.criterion"
title: "harness.criterion"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.criterion"
generated: true
---

# harness.criterion

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_criterion___init__|The criterion plane: materialize from trusted provenance, execute, produce a verdict.]]
- **contains** → [[module__harness_criterion_execute|Run a criterion hermetically and classify what happened three ways.]]
- **contains** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **contains** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]]
- **contains** → [[module__harness_criterion_test_execute|Three outcomes, and the ways two of them get silently collapsed into one.]]
- **contains** → [[module__harness_criterion_test_materialize|A1, asserted as an architectural claim rather than as a list of blocked filenames.]]
- **contains** → [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]]
