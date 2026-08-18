---
kind: module
id: "module:migrations.roles.002_grants.sql"
title: "migrations/roles/002_grants.sql"
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "migrations/roles/002_grants.sql:1"
extractor: "code"
tags: [protected]
aliases:
  - "migrations.roles.002_grants.sql"
  - "migrations/roles/002_grants.sql"
generated: true
---

# migrations/roles/002_grants.sql

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/roles/002_grants.sql:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | migrations/roles/002_grants.sql |
| `tree` | migrations |

## Enforced by (code)

- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — Sole author of verdicts is CriterionRunner (D5, D39). The harness may
- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — read them and may not write them, which is the separation D39 makes
- [[decision__D5|The harness executes checks, never the agent]] **enforced_by** → this — Sole author of verdicts is CriterionRunner (D5, D39). The harness may
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — D51. This INSERT is alfred_operator's only INSERT anywhere in the
