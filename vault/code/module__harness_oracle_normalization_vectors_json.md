---
kind: module
id: "module:harness.oracle.normalization_vectors.json"
title: "harness/oracle/normalization_vectors.json"
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle/normalization_vectors.json:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.oracle.normalization_vectors.json"
  - "harness/oracle/normalization_vectors.json"
generated: true
---

# harness/oracle/normalization_vectors.json

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle/normalization_vectors.json:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/oracle/normalization_vectors.json |
| `tree` | harness |

## Binds

- [[module__harness_oracle|harness.oracle]] **contains** → this

## Enforced by (code)

- [[decision__D54|D50 is enforced by an environment split, not by a check alone: the oracle's outputs cross ]] **enforced_by** → this — "oracle image, where it must, because D54 forbids the oracle's source crossing the",
