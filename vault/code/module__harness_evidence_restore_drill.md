---
kind: module
id: "module:harness.evidence.restore_drill"
title: "D-synthetic: dump one cluster, restore into another, and check four ways."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/restore_drill.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "D-synthetic: dump one cluster, restore into another, and check four ways."
  - "harness.evidence.restore_drill"
generated: true
---

# D-synthetic: dump one cluster, restore into another, and check four ways.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/restore_drill.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/evidence/restore_drill.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- **imports** → [[module__harness_evidence_anchor|The chain head, recorded off-machine, and derived by the implementation that is not Python]]
- **imports** → [[module__harness_evidence_export|Dump a chain as raw columns, so something else can check it.]]
- [[module__harness_evidence|harness.evidence]] **contains** → this
- [[module__harness_evidence_test_restore_drill|The restore drill and the independent re-walk, each with the control that matters.]] **imports** → this
- [[module__harness_evidence_test_table_binding|Every chained table is drill-covered.]] **imports** → this
