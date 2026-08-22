---
kind: module
id: "module:harness.db.test_pinned_postgres_image"
title: "Dev compose and the CI grant matrix must run one Postgres, and only a comment said so."
shape: "module"
present: "true"
protected: "true"
lint_gated: "false"
source: "harness/db/test_pinned_postgres_image.py:1"
extractor: "code"
tags: [protected]
aliases:
  - "Dev compose and the CI grant matrix must run one Postgres, and only a comment said so."
  - "harness.db.test_pinned_postgres_image"
generated: true
---

# Dev compose and the CI grant matrix must run one Postgres, and only a comment said so.

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `harness/db/test_pinned_postgres_image.py:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | true |
| `path` | harness/db/test_pinned_postgres_image.py |
| `tree` | harness |

## Binds

- **imports** → [[module__harness_db_cluster|Throwaway Postgres cluster: create, migrate, assert against, destroy.]]
- [[module__harness_db|harness.db]] **contains** → this

## Enforced by (code)

- [[decision__D57|The harness self-test suites are two-sided, and each carries a stated vacuity control]] **enforced_by** → this — # Vacuity guard (D57): a parser that finds nothing agrees with nothing. The equality
