---
kind: module
id: "module:harness.criterion.test_runner"
title: "Verdict composition, with the two collapses that would make the number meaningless."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/criterion/test_runner.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Verdict composition, with the two collapses that would make the number meaningless."
  - "harness.criterion.test_runner"
generated: true
---

# Verdict composition, with the two collapses that would make the number meaningless.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/criterion/test_runner.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/criterion/test_runner.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_execute|Run a criterion hermetically and classify what happened three ways.]]
- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **imports** → [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]]
- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- [[module__harness_criterion|harness.criterion]] **contains** → this

## Enforced by (code)

- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — """D49: a task the visible half alone would accept is not schedulable."""
- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — """The structural decision, asserted rather than described.

    The harvest command reads every file in its own directo
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Verdict composition, with the two collapses that would make the number meaningless.

**How this suite would be shown 
