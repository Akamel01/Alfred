---
kind: module
id: "module:harness.evidence.export"
title: "Dump a chain as raw columns, so something else can check it."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/export.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Dump a chain as raw columns, so something else can check it."
  - "harness.evidence.export"
generated: true
---

# Dump a chain as raw columns, so something else can check it.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/export.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/evidence/export.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- [[module__harness_evidence|harness.evidence]] **contains** → this
- [[module__harness_evidence_restore_drill|D-synthetic: dump one cluster, restore into another, and check four ways.]] **imports** → this
- [[module__harness_evidence_test_restore_drill|The restore drill and the independent re-walk, each with the control that matters.]] **imports** → this
