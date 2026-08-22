---
kind: module
id: "module:harness.verdicts"
title: "harness.verdicts"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/verdicts:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.verdicts"
generated: true
---

# harness.verdicts

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/verdicts:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_verdicts___init__|The harness's verdict vocabulary: the words, the stamp bridge table, one home.]]
- **contains** → [[module__harness_verdicts_test_verdicts|The verdict vocabulary's bindings: every other spelling answers to this module.]]
- [[module__harness_criterion_runner|Compose one verdict, and keep the held-out half out of the environment that runs.]] **imports** → this
- [[module__harness_verdicts_test_verdicts|The verdict vocabulary's bindings: every other spelling answers to this module.]] **imports** → this
- [[module__tests_test_stamp_verify|The two-stage read, its five outcomes, and the bridge to failure semantics (ADR-0006).]] **imports** → this
- [[gate-step__inspector_14|Verdict vocabulary (words, stamp bridge table, authority bindings)]] **runs** → this
