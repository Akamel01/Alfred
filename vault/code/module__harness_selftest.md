---
kind: module
id: "module:harness.selftest"
title: "harness.selftest"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/selftest:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.selftest"
generated: true
---

# harness.selftest

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/selftest:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_selftest___init__|harness/selftest/__init__.py]]
- **contains** → [[module__harness_selftest_failure_register_json|harness/selftest/failure_register.json]]
- **contains** → [[module__harness_selftest_noise|Measures ε. It is never chosen, and this is the module that makes that true.]]
- **contains** → [[module__harness_selftest_replay_fixtures|A synthetic source and a synthetic metric, so the replay harness can be exercised.]]
- **contains** → [[module__harness_selftest_stage_gate_register_json|harness/selftest/stage_gate_register.json]]
- **contains** → [[module__harness_selftest_suites|The two suites. They are one module because they are each other's vacuity control.]]
- **contains** → [[module__harness_selftest_synthetic|A criterion with no domain in it, and a defect that can be dialled.]]
- **contains** → [[module__harness_selftest_test_replay|Byte-identical deterministic replay, and the control that stops it being trivial.]]
- **contains** → [[module__harness_selftest_test_selftest|S4. The inspector's inspector, and the controls that stop it reading green for free.]]
- [[gate-step__inspector_09|Harness self-test (null-agent floor, seeded-defect ladder, controls)]] **runs** → this
