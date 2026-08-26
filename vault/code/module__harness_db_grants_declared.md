---
kind: module
id: "module:harness.db.grants_declared"
title: "`migrations/roles/grants.yaml`, parsed and expanded into concrete grant tuples."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db/grants_declared.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "`migrations/roles/grants.yaml`, parsed and expanded into concrete grant tuples."
  - "harness.db.grants_declared"
generated: true
---

# `migrations/roles/grants.yaml`, parsed and expanded into concrete grant tuples.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db/grants_declared.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/db/grants_declared.py |
| `tree` | harness |

## Binds

- [[module__harness_db|harness.db]] **contains** → this
- [[module__harness_db_assert_grants|Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`.]] **imports** → this
- [[module__tests_parser_test_grants_declared|Tests for `grants_declared` parser.]] **imports** → this
