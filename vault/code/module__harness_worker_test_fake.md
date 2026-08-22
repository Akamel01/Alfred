---
kind: module
id: "module:harness.worker.test_fake"
title: "Rehearsals of the `Worker` seam against the in-memory adaptor — interface only."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker/test_fake.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Rehearsals of the `Worker` seam against the in-memory adaptor — interface only."
  - "harness.worker.test_fake"
generated: true
---

# Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/test_fake.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/worker/test_fake.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_fingerprint_record|The run fingerprint record: what a run was measured on, stated once and hashed.]]
- **imports** → [[module__harness_worker_fake|The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics.]]
- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_worker|harness.worker]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """The fake wires the port's own `check_handle`, at the default MEASUREMENT
    strictness — so every refusal text is th
