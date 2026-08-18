---
kind: module
id: "module:harness.containment.assertions"
title: "Three outcomes for a containment assertion, and the third is the dangerous one."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/assertions.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Three outcomes for a containment assertion, and the third is the dangerous one."
  - "harness.containment.assertions"
generated: true
---

# Three outcomes for a containment assertion, and the third is the dangerous one.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/assertions.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/assertions.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0007|Executor-premise assertions may pass vacuously, and that is a third outcome]] **enforced_by** → this — """Three outcomes for a containment assertion, and the third is the dangerous one.

`passed` and `failed` are obvious. *
