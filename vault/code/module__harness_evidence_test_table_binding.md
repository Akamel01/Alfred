---
kind: module
id: "module:harness.evidence.test_table_binding"
title: "Every chained table is drill-covered."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/test_table_binding.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Every chained table is drill-covered."
  - "harness.evidence.test_table_binding"
generated: true
---

# Every chained table is drill-covered.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/test_table_binding.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/evidence/test_table_binding.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_evidence_restore_drill|D-synthetic: dump one cluster, restore into another, and check four ways.]]
- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- [[module__harness_evidence|harness.evidence]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """Every chained table is drill-covered.

The store chains exactly `CHAINED_TABLES`; the restore drill dumps, restores a
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # Vacuity guards first (D57): two empty collections are subsets of each other and
