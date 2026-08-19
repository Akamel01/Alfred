---
kind: module
id: "module:harness.oracle.run"
title: "Runs the oracle image. Outside the container, and it never imports the oracle."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/run.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Runs the oracle image. Outside the container, and it never imports the oracle."
  - "harness.oracle.run"
generated: true
---

# Runs the oracle image. Outside the container, and it never imports the oracle.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/run.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/oracle/run.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_oracle_pins|What the oracle environment is pinned to, and the platform finding that forced it.]]
- [[module__harness_oracle|harness.oracle]] **contains** → this
- [[module__harness_oracle_test_oracle|Tests for the oracle boundary. Most run without the image; the slow one needs it.]] **imports** → this

## Enforced by (code)

- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — """Runs the oracle image. Outside the container, and it never imports the oracle.

D54's split is that the oracle's outp
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """Runs the oracle image. Outside the container, and it never imports the oracle.

D54's split is that the oracle's outp
- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """Run the fingerprint emitter and refuse a run whose normalization disagrees with ours.

    Same posture as `run_oracl
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # D57. Zero vectors answered is not agreement; it is a cross-check that did not run.
