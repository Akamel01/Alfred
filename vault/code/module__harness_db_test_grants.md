---
kind: module
id: "module:harness.db.test_grants"
title: "The grant matrix, asserted two ways: by set equality, and by being refused."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db/test_grants.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "The grant matrix, asserted two ways: by set equality, and by being refused."
  - "harness.db.test_grants"
generated: true
---

# The grant matrix, asserted two ways: by set equality, and by being refused.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db/test_grants.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/db/test_grants.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_db_assert_grants|Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`.]]
- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- [[module__harness_db|harness.db]] **contains** → this

## Enforced by (code)

- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — # The harness may read a verdict and may not write one. D39 makes that physical:
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — "D39-harness-verdict-insert"
- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — """The grant matrix, asserted two ways: by set equality, and by being refused.

**Every denial asserts `SQLSTATE 42501` 
