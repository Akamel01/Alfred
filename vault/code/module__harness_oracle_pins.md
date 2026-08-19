---
kind: module
id: "module:harness.oracle.pins"
title: "What the oracle environment is pinned to, and the platform finding that forced it."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/pins.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "What the oracle environment is pinned to, and the platform finding that forced it."
  - "harness.oracle.pins"
generated: true
---

# What the oracle environment is pinned to, and the platform finding that forced it.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/pins.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/oracle/pins.py |
| `tree` | harness |

## Binds

- [[module__harness_oracle|harness.oracle]] **contains** → this
- [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]] **imports** → this
- [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]] **imports** → this
- [[module__harness_oracle_test_oracle|Tests for the oracle boundary. Most run without the image; the slow one needs it.]] **imports** → this

## Enforced by (code)

- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — """What the oracle environment is pinned to, and the platform finding that forced it.

D54: the oracle lives in one offl
