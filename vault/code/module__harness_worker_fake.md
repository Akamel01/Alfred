---
kind: module
id: "module:harness.worker.fake"
title: "The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/worker/fake.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics."
  - "harness.worker.fake"
generated: true
---

# The in-memory `Worker`: a scripted stand-in that rehearses the seam's semantics.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/worker/fake.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/worker/fake.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_worker|harness.worker]] **contains** → this
- [[module__harness_worker_test_fake|Rehearsals of the `Worker` seam against the in-memory adaptor — interface only.]] **imports** → this
