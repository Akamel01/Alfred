---
kind: module
id: "module:harness.evidence.test_restore_drill"
title: "The restore drill and the independent re-walk, each with the control that matters."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/evidence/test_restore_drill.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The restore drill and the independent re-walk, each with the control that matters."
  - "harness.evidence.test_restore_drill"
generated: true
---

# The restore drill and the independent re-walk, each with the control that matters.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/evidence/test_restore_drill.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/evidence/test_restore_drill.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- **imports** → [[module__harness_evidence_anchor|The chain head, recorded off-machine, and derived by the implementation that is not Python]]
- **imports** → [[module__harness_evidence_export|Dump a chain as raw columns, so something else can check it.]]
- **imports** → [[module__harness_evidence_restore_drill|D-synthetic: dump one cluster, restore into another, and check four ways.]]
- **imports** → [[module__harness_evidence_store|Append-only, hash-chained evidence writes.]]
- [[module__harness_evidence|harness.evidence]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """The restore drill and the independent re-walk, each with the control that matters.

**How this suite would be shown v
