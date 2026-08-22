---
kind: module
id: "module:harness.verdicts.test_verdicts"
title: "The verdict vocabulary's bindings: every other spelling answers to this module."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/verdicts/test_verdicts.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The verdict vocabulary's bindings: every other spelling answers to this module."
  - "harness.verdicts.test_verdicts"
generated: true
---

# The verdict vocabulary's bindings: every other spelling answers to this module.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/verdicts/test_verdicts.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/verdicts/test_verdicts.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_verdicts|harness.verdicts]]
- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_verdicts|harness.verdicts]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0006|The result stamp field set, its own version, and upstream toolchain provenance]] **enforced_by** → this — # The five rows ADR-0006 specifies, restated here rather than read from the module under
