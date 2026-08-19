---
kind: module
id: "module:harness.oracle.test_oracle"
title: "Tests for the oracle boundary. Most run without the image; the slow one needs it."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/test_oracle.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Tests for the oracle boundary. Most run without the image; the slow one needs it."
  - "harness.oracle.test_oracle"
generated: true
---

# Tests for the oracle boundary. Most run without the image; the slow one needs it.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/test_oracle.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/oracle/test_oracle.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]]
- **imports** → [[module__harness_oracle_pins|What the oracle environment is pinned to, and the platform finding that forced it.]]
- **imports** → [[module__harness_oracle_points|The questions put to the oracle, and where each one came from.]]
- **imports** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]]
- [[module__harness_oracle|harness.oracle]] **contains** → this

## Enforced by (code)

- [[decision__D49|A grading point is admitted by the provenance of its authorship, not by whether the oracle]] **enforced_by** → this — # --------------------------------------------------------------- D49 admissibility
