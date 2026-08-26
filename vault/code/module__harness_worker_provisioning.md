---
kind: module
id: "module:harness.worker.provisioning"
title: "Provisioning for the OpenHands adaptor runtime."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker/provisioning.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Provisioning for the OpenHands adaptor runtime."
  - "harness.worker.provisioning"
generated: true
---

# Provisioning for the OpenHands adaptor runtime.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/provisioning.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/worker/provisioning.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_worker|harness.worker]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Run boot-time containment assertions inside the container.

    These assertions MUST execute inside the container an
