---
kind: module
id: "module:harness.containment.handle"
title: "The one crossing from probe vocabulary to handle vocabulary."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/handle.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The one crossing from probe vocabulary to handle vocabulary."
  - "harness.containment.handle"
generated: true
---

# The one crossing from probe vocabulary to handle vocabulary.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/handle.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/handle.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_assertions|Three outcomes for a containment assertion, and the third is the dangerous one.]]
- **imports** → [[module__harness_worker_port|The `Worker` port. A claim crosses it, or an exception does — never a verdict.]]
- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_test_c_assertions|C1–C15 beyond the two probes, each paired with the control that stops it reading green.]] **imports** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """The one crossing from probe vocabulary to handle vocabulary.

Two `Assertion` types exist and both are right. `harnes
