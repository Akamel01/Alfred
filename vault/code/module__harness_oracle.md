---
kind: module
id: "module:harness.oracle"
title: "harness.oracle"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/oracle:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.oracle"
generated: true
---

# harness.oracle

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/oracle:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_oracle___init__|harness/oracle/__init__.py]]
- **contains** → [[module__harness_oracle_extract|Runs INSIDE the oracle image. Computes what CriMe says, and nothing else.]]
- **contains** → [[module__harness_oracle_fingerprints|Runs INSIDE the oracle image. Emits digests and names, and never the source itself.]]
- **contains** → [[module__harness_oracle_load|Carries oracle values across the boundary as data, and refuses when they are not clean.]]
- **contains** → [[module__harness_oracle_normalization_vectors_json|harness/oracle/normalization_vectors.json]]
- **contains** → [[module__harness_oracle_pins|What the oracle environment is pinned to, and the platform finding that forced it.]]
- **contains** → [[module__harness_oracle_points|The questions put to the oracle, and where each one came from.]]
- **contains** → [[module__harness_oracle_run|Runs the oracle image. Outside the container, and it never imports the oracle.]]
- **contains** → [[module__harness_oracle_test_oracle|Tests for the oracle boundary. Most run without the image; the slow one needs it.]]
- [[gate-step__inspector_10|Oracle boundary (pins, refusals, admissibility)]] **runs** → this
