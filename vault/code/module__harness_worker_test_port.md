---
kind: module
id: "module:harness.worker.test_port"
title: "The Worker port's structural refusals, and the control on the check that enforces them."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker/test_port.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The Worker port's structural refusals, and the control on the check that enforces them."
  - "harness.worker.test_port"
generated: true
---

# The Worker port's structural refusals, and the control on the check that enforces them.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/test_port.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/worker/test_port.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_worker|harness.worker]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """A worker that requires nothing has been configured to check nothing, and from
    outside that is indistinguishable f
