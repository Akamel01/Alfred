---
kind: module
id: "module:harness.worker"
title: "harness.worker"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.worker"
generated: true
---

# harness.worker

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | false |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_worker___init__|harness/worker/__init__.py]]
- **contains** → [[module__harness_worker_fake|The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics.]]
- **contains** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- **contains** → [[module__harness_worker_test_fake|Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.]]
- **contains** → [[module__harness_worker_test_port|The Worker port's structural refusals, and the control on the check that enforces them.]]
- [[gate-step__inspector_12|Worker port (claim/fault split, containment refusals)]] **runs** → this
