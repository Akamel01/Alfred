---
kind: module
id: "module:harness.db"
title: "harness.db"
shape: "package"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db:1"
extractor: "code"
tags: [protected]
aliases:
  - "harness.db"
generated: true
---

# harness.db

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db:1`

## Fields

| Field | Value |
|---|---|
| `namespace_package` | true |
| `tree` | harness |

## Binds

- **contains** → [[module__harness_db_assert_grants|Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`.]]
- **contains** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- **contains** → [[module__harness_db_grants_declared|`migrations/roles/grants.yaml`, parsed and expanded into concrete grant tuples.]]
- **contains** → [[module__harness_db_test_cluster|Tests of the fixture itself, before anything is asserted through it.]]
- **contains** → [[module__harness_db_test_grants|The grant matrix, asserted two ways: by set equality, and by being refused.]]
- [[gate-step__database_04|Throwaway cluster, roles, grants and migrations]] **runs** → this
