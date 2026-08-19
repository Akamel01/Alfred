---
kind: module
id: "module:harness.selftest.test_selftest"
title: "S4. The inspector's inspector, and the controls that stop it reading green for free."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest/test_selftest.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "S4. The inspector's inspector, and the controls that stop it reading green for free."
  - "harness.selftest.test_selftest"
generated: true
---

# S4. The inspector's inspector, and the controls that stop it reading green for free.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest/test_selftest.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/selftest/test_selftest.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_criterion_materialize|Build the criterion environment from an allowlist, never from the candidate tree.]]
- **imports** → [[module__harness_selftest_noise|Measures ε. It is never chosen, and this is the module that makes that true.]]
- **imports** → [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]]
- [[module__harness_selftest|harness.selftest]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0015|A missing candidate file is the candidate's failure, not the harness's fault]] **enforced_by** → this — """The defect this suite found on its first run. `materialize` used to raise on an
    absent candidate path, which a ca
