---
kind: module
id: "module:harness.criterion.runner"
title: "Compose one verdict, and keep the held-out half out of the environment that runs."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion/runner.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Compose one verdict, and keep the held-out half out of the environment that runs."
  - "harness.criterion.runner"
generated: true
---

# Compose one verdict, and keep the held-out half out of the environment that runs.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion/runner.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/criterion/runner.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_execute|Run a criterion hermetically and classify what happened three ways.]]
- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- **imports** → [[module__harness_verdicts|harness.verdicts]]
- [[module__harness_criterion|harness.criterion]] **contains** → this
- [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] **imports** → this
- [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]] **imports** → this

## Enforced by (code)

- [[decision__D33|Graduation calibrates on held-out pass rate only]] **enforced_by** → this — # decide acceptance — which is the calibration failure D33 exists to prevent.
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — """Sole author of verdicts (D5, D39).

    Holds `alfred_criterion` — the only role with any privilege on `heldout`, and
- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — # D49: every schedulable task carries at least one held-out grading point. A task
- [[decision__D5|The harness executes checks, never the agent]] **enforced_by** → this — """Sole author of verdicts (D5, D39).

    Holds `alfred_criterion` — the only role with any privilege on `heldout`, and
- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — """Compose one verdict, and keep the held-out half out of the environment that runs.

**The structural decision in this 
