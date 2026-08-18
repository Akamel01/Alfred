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
