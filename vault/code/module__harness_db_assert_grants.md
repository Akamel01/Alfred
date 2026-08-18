---
kind: module
id: "module:harness.db.assert_grants"
title: "Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db/assert_grants.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`."
  - "harness.db.assert_grants"
generated: true
---

# Assert the cluster's grant matrix **equals** `migrations/roles/grants.yaml`.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db/assert_grants.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | harness/db/assert_grants.py |
| `tree` | harness |

## Binds

- [[module__harness_db|harness.db]] **contains** → this
