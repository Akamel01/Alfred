---
kind: module
id: "module:harness.db.cluster"
title: "Throwaway Postgres cluster: create, migrate, assert against, destroy."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db/cluster.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Throwaway Postgres cluster: create, migrate, assert against, destroy."
  - "harness.db.cluster"
generated: true
---

# Throwaway Postgres cluster: create, migrate, assert against, destroy.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db/cluster.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/db/cluster.py |
| `tree` | harness |

## Binds

- [[module__harness_db|harness.db]] **contains** → this
- [[module__harness_criterion_test_runner|Verdict composition, with the two collapses that would make the number meaningless.]] **imports** → this
- [[module__harness_db_test_cluster|Tests of the fixture itself, before anything is asserted through it.]] **imports** → this
- [[module__harness_db_test_grants|The grant matrix, asserted two ways: by set equality, and by being refused.]] **imports** → this
- [[module__harness_db_test_pinned_postgres_image|Dev compose and the CI grant matrix must run one Postgres, and only a comment said so.]] **imports** → this
- [[module__harness_evidence_restore_drill|D-synthetic: dump one cluster, restore into another, and check four ways.]] **imports** → this
- [[module__harness_evidence_test_restore_drill|The restore drill and the independent re-walk, each with the control that matters.]] **imports** → this
- [[module__harness_evidence_test_store|The append-only chain, asserted from both sides.]] **imports** → this
