---
kind: module
id: "module:harness.containment.test_dispatch_mount"
title: "Tests for dispatch mount exclusion (C12/C13)."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/containment/test_dispatch_mount.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Tests for dispatch mount exclusion (C12/C13)."
  - "harness.containment.test_dispatch_mount"
generated: true
---

# Tests for dispatch mount exclusion (C12/C13).

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/containment/test_dispatch_mount.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/containment/test_dispatch_mount.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_containment_dispatch_mount|Dispatch mount exclusion for C12/C13 containment assertions.]]
- **imports** → [[module__harness_containment_inside|C8, C9, C12, C13 — the assertions that need no executor vocabulary.]]
- [[module__harness_containment|harness.containment]] **contains** → this

## Enforced by (code)

- [[adr__ADR-0035|The protected set's single home names its fourth shape as a projection, not a second autho]] **enforced_by** → this — """Tests for dispatch mount exclusion (C12/C13).

Prototype for ADR-0035: dispatch mount must be excluded from "no unexp
