---
kind: module
id: "module:harness.containment.dispatch_mount"
title: "Dispatch mount exclusion for C12/C13 containment assertions."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/dispatch_mount.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Dispatch mount exclusion for C12/C13 containment assertions."
  - "harness.containment.dispatch_mount"
generated: true
---

# Dispatch mount exclusion for C12/C13 containment assertions.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/dispatch_mount.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/containment/dispatch_mount.py |
| `tree` | harness |

## Binds

- [[module__harness_containment|harness.containment]] **contains** → this
- [[module__harness_containment_inside|C8, C9, C12, C13 — the assertions that need no executor vocabulary.]] **imports** → this
- [[module__harness_containment_test_dispatch_mount|Tests for dispatch mount exclusion (C12/C13).]] **imports** → this
