---
kind: module
id: "module:migrations.roles.grants.yaml"
title: "migrations/roles/grants.yaml"
shape: "file"
present: "true"
protected: "true"
lint_gated: "false"
source: "migrations/roles/grants.yaml:1"
extractor: "code"
tags: [protected]
aliases:
  - "migrations.roles.grants.yaml"
  - "migrations/roles/grants.yaml"
generated: true
---

# migrations/roles/grants.yaml

> [!warning] Generated — do not edit
> This note is emitted by `tools/gen_vault.py` from the repository. Edit the source, then regenerate. `gen_vault.py --check` fails on a hand edit.

**Source** · `migrations/roles/grants.yaml:1`

## Fields

| Field | Value |
|---|---|
| `is_test` | false |
| `path` | migrations/roles/grants.yaml |
| `tree` | migrations |

## Enforced by (code)

- [[decision__D39|structural enforcement of D16/D20 (from gstack, the one idea that stands alone)]] **enforced_by** → this — sole author of verdicts (D5, D39)
- [[decision__D5|The harness executes checks, never the agent]] **enforced_by** → this — sole author of verdicts (D5, D39)
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — Mission control command surface (D51). Its ONLY INSERT anywhere in the cluster is
- [[decision__D51|Mission control exists, it is split, and every operator action is an evidence row]] **enforced_by** → this — Mission control read model (D51) — agents may build it. SELECT and nothing else,
