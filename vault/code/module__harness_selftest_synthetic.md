---
kind: module
id: "module:harness.selftest.synthetic"
title: "A criterion with no domain in it, and a defect that can be dialled."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest/synthetic.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "A criterion with no domain in it, and a defect that can be dialled."
  - "harness.selftest.synthetic"
generated: true
---

# A criterion with no domain in it, and a defect that can be dialled.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest/synthetic.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/selftest/synthetic.py |
| `tree` | harness |

## Binds

- [[module__harness_selftest|harness.selftest]] **contains** → this
- [[module__harness_selftest_noise|Measures ε. It is never chosen, and this is the module that makes that true.]] **imports** → this
- [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0011|The criterion subprocess computes; the runner compares]] **enforced_by** → this — # beside the code under test is D50's delegation failure (ADR-0011).
- [[decision__D50|The oracle is absent from the execution plane by assertion, not by convention]] **enforced_by** → this — # beside the code under test is D50's delegation failure (ADR-0011).
